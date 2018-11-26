"""
Author      : Vivek KC
Email       : devops@vera.com
Date        : Tue Aug 14 13:42:39 UTC 2018

Description : This script helps in rolling restarting Elasticsearch cluster nodes safely, making sure the cluster \
                is green always. This takes one node at a time, process it and wait for the cluster to turn green

Note        : This script was inspired by - http://decisionlab.io/blog/2017/02/12/restarting-es

"""
import datetime
import requests
import logging
import json
import sys
import os
import time
import argparse

# # Fabric remote exec
import fabric.api as fab
from fabric.network import disconnect_all
# from fabric.api import warn_only
# from fabric import exceptions
from contextlib import contextmanager
#####################################


class FabricException(Exception):
    pass


class VeraElasticRoller(object):
    """
    This is the main class that manages the whole activity.
    """
    # Track how long we take to finish each node.
    start_time = time.time()

    def __init__(self, server=None, ssh_key=None, user=None, options=None):
        """
        :param server:
        :param ssh_key:
        :param user:
        """
        self.ssh_key = ssh_key
        self.server = server
        self.user = user

        self.options = options

        # Add anything to exclude in a list. Or pass a CSV by --exclude
        '''
        self.exclude_default = ['prod-west2-es6.localdomain',
                              'prod-west2-es7.localdomain',
                              'prod-west2-es8.localdomain',
                              'prod-west2-es9.localdomain',
                              'prod-west2-es10.localdomain',
                              'prod-west2-es11.localdomain',
                              'prod-west2-es12.localdomain',
                              'prod-west2-es13.localdomain',
                              'prod-west2-es14.localdomain',
                              'prod-west2-es15.localdomain',
                              'prod-west2-es16.localdomain',
                              'prod-west2-es17.localdomain',
                              'prod-west2-es18.localdomain',
                              'prod-west2-es19.localdomain',
                              'prod-west2-es20.localdomain'
                            ]
        '''
        self.exclude_default = []

        """
        Relevant Elasticsearch roles.

        Note 1: These values appear under the 'roles' field in the response object
          for _nodes in the api.

        Note 2: Order matters here, as we want to restart masters first.

        Note 3: Keep an 'other' category because Elastic is liable to add/remove

        PS: For Vera, the nodes does not look classified - all are falling into other!
        """
        self.es_roles = ['master', 'client', 'data', 'other']
        self.logfile = 'cluster_restart-' + time.strftime('%Y_%m_%d_%H_%M' + '.log')

        self.logger = self.setup_logging()
        self.logger.info("Beginning ES cluster rolling restart for Vera!!!")

        self.elected_master = self.get_elected_master()

    def do_request(self, server=None, verb=None, verify=False, data=None):
        if server is None:
            self.logger.error("you must pass a servername with server=hostname, exiting!")
            sys.exit(1)

        attempts = 5
        while attempts > 0:
            try:
                r = requests.request(verb.upper(), server, verify=verify, data=data)

                # Handle HTTP 400 errors, i.e. wrong password.
                if str(r.status_code).startswith('4'):
                    self.logger.error("Request to '{0}' returned HTTP {1}. Credentials correct?".
                                      format(self.server, r.status_code))
                    sys.exit(1)
            except requests.exceptions.ConnectionError:
                attempts -= 1
                self.logger.warn("Attempted connection to {0} failed. Trying {1} more times".
                             format(self.server, attempts))
                time.sleep(5)
            except Exception as e:
                self.logger.error('Something went wrong for remote call: method="{}", data={}, error={}'.
                              format(verb.upper(), data, e))
                sys.exit(1)

            return r

    def get_cluster_state(self, wait=300):
        while True:
            r = self.do_request(verb='get',
                                server='http://{0}:9200/_cluster/health'.format(self.server),
                                verify=False)
            json_data = json.loads(r.text)
            state = str(json_data["status"])

            if state == 'green':
                self.logger.info("GOOD - Cluster State has turned: GREEN!")
                break
            else:
                self.logger.info('WARN - Cluster State is yet: {}, sleeping for {}sec..'.format(state.upper(), wait))
                time.sleep(wait)

            shards_unassigned = self.check_cluster_param(server=self.server, param='unassigned_shards')
            if shards_unassigned > 0:
                self.logger.info('WARN: There are "{}" unassigned shards yet, forcing enable..'.format(shards_unassigned))
                self.shards_allocation_action(options.server, 'enable')

    def check_nodes_up(self, count=15, wait=60):
        while True:
            r = self.do_request(verb='get',
                                server='http://{0}:9200/_cluster/health'.format(self.server),
                                verify=False)
            json_data = json.loads(r.text)
            node_count = int(json_data["number_of_nodes"])

            if node_count == count:
                self.logger.info("GOOD - all " + str(node_count) + " nodes in the Cluster are up:!")
                break
            else:
                self.logger.info('WARN - Only {0} nodes of {1} are up, sleeping for {2}sec..'.format(node_count, count, wait))
                time.sleep(wait)

    def check_cluster_param(self, param):
            r = self.do_request(verb='get',
                                server='http://{0}:9200/_cluster/health'.format(self.server),
                                verify=False)

            json_data = json.loads(r.text)
            count_x = -1
            if param != '' and param in json_data:
                count_x = int(json_data[param])
                self.logger.info("Component={} in the Cluster are {}!".format(param, count_x))

            return count_x

    def update_cluster_param(self, verb='put', endpoint='_cluster/settings', data=None):
        # self.logger.debug("Data is " + data)
        try:
            r = self.do_request(verb=verb,
                                server='http://{0}:9200/{1}'.format(self.server, endpoint),
                                verify=False,
                                data=data)
            self.logger.info('Done cluster update: method={}, endpoint={}, data={}, result={}'.
                             format(verb.upper(), endpoint, data, r.text))
        except Exception as e:
            self.logger.error('Something went wrong for method="{}", at endpoint={}, data={}, error={}'.
                          format(verb.upper(), endpoint, data, e))
            sys.exit(1)

    def get_cluster_nodes(self, excluded=[], master_domain=''):
        nodelist_len = 0
        nodelist = {}
        for role in self.es_roles:
            nodelist[role] = []

        self.logger.info("Requesting node list from cluster")
        r = self.do_request(verb='get',
                            server='http://{0}:9200/_nodes'.format(self.server),
                            verify=False)
        json_data = json.loads(r.text)

        # Build our dict from the response data.
        for node, values in json_data["nodes"].items():
            # Don't consider nodes that's in the exclude list.
            self.logger.debug("Try exclude with possible short name as well: " + values['name'].split(".")[0])
            if values['name'] in excluded or values['name'].split(".")[0] in excluded:
                self.logger.debug("Node - " + values['name'] + " (" + node + ") is excluded explicitly!")
                continue

            has_role = False
            for role in self.es_roles:
                if 'roles' in values and role in values['roles']:
                    has_role = True
                    nodelist[role].append(values['name'])
                    nodelist_len += 1
                    break

            # Node has a role that we're unaware of. Put it in 'other'.
            if not has_role:
                nodelist['other'].append(values['name'])
                nodelist_len += 1

        # Sort each list of nodes for easier processing and tracking.
        for role in self.es_roles:
            nodelist[role].sort()

        # We want to restart the Elected Master last, so put its entry
        # at the end of the list of masters.

        if 'master' in nodelist and len(nodelist['master']) != 0:
            print("master is not empty.. why")
            elected_master_position = nodelist['master'].index(self.elected_master)
            # Swap the elected master entry with whatever is currently at the end of the list.
            nodelist['master'][-1], nodelist['master'][elected_master_position] \
                = nodelist['master'][elected_master_position], nodelist['master'][-1]
        else:
            elected_master_position = nodelist['other'].index(self.elected_master)
            self.logger.info('Elected master is {} at position#{}'.
                             format(self.elected_master, elected_master_position))

            # Push master node end of the list, so that it will be processed last
            self.logger.debug('Moving master node at the bottom of the list, that to be processed only at the end!')
            nodelist['other'].remove(self.elected_master)
            nodelist['other'].append(self.elected_master)

        self.logger.info("Obtained list of {0} nodes".format(nodelist_len))
        for role in self.es_roles:
            self.logger.info('=== {0} - {1} nodes ==='.format(role, len(nodelist[role])))
            for node in nodelist[role]:
                self.logger.info(node)

        return nodelist

    def get_elected_master(self):
        r = self.do_request(verb='get',
                            server='http://{0}:9200/_nodes/_master'.format(self.server),
                            verify=False)
        json_data = json.loads(r.text)

        # There should only be a single elected master.
        master_node = None
        for nodename, values in json_data['nodes'].items():
            master_node = values['name']

        return master_node

    def restart_es_node(self, node=None):
        self.logger.info('ToDO - restart the node: {}'.format(node))
        print('''\n\t1. SSH to the node: sshprod ec2-user@{0}\n
        \t2. Exec: curl -XPOST 'http://localhost:9200/_cluster/nodes/_local/_shutdown'\n
        \t3. sudo reboot\n'''.format(node))

        self.wait_for_confirmation(msg='Node reboot waiting')
        time.sleep(5)

    def shards_allocation_action(self, action=''):
        disable_shards_data = '{"transient": {"cluster.routing.allocation.enable": "none"}}'
        enable_shards_data = '{"transient": {"cluster.routing.allocation.enable": "all"}}'

        if action == 'disable':
            data = disable_shards_data
        elif action == 'enable':
            data = enable_shards_data
        else:
            self.logger.error('Undetermined action="{}", should be either of enable|disable!'.format(action))
            sys.exit(1)

        self.logger.debug('Doing - shards "{}", with data="{}"'.format(action, data))
        try:
            r = self.do_request(verb='put',
                                server='http://{0}:9200/_cluster/settings'.format(self.server),
                                data=data)
            self.logger.info('Done Shards Allocation "{}": {}'.format(action.upper(), r.text))
        except Exception as e:
            self.logger.error('Something went wrong for action="{}", with data="{}", with error="{}'.
                          format(action, data, e))
            sys.exit(1)

    def wait_for_confirmation(self, msg='Waiting'):
        while True:
            choice = raw_input('INFO: {0}, needs confirmation to proceed. When ready say "yes": '.format(msg))

            if choice == 'yes':
                break
            else:
                print('Ahh - wrong choice "{}". I am told to wait until you tell me "yes"!'.format(choice))

    def ssh_remote_exec(self, host=None, command=None):
        self.logger.info('WARN: Executing "{}" on remote host "{}"'.format(command, host))

        if self.options.dry_run is True:
            self.logger.info('Dry-run: skipping remote execution..')
        else:
            with self.ssh(fab.settings(host_string=host, user=self.user, key_filename=self.ssh_key, warn_only=True)):
                return fab.sudo(command, pty=False)

    @contextmanager
    def ssh(self, settings):
        with settings:
            yield

    def prepare_shutdown(self, hostname=None, ip=None):
        host = hostname
        if ip is not None:
            host = ip

        try:
            for command in self.options.remote_cmd:
                output = self.ssh_remote_exec(host, command)
        except FabricException as e:
            self.logger.error('Failed to exec "{0}" on remote host "{1}", error:{}'.
                          format(self.remote.remote_cmd, host, e))
            sys.exit(10)
        finally:
            disconnect_all()

        return output

    def populate_nodes_fromfile(self):
        """ Not implemented """
        pass

    def update_balance_threshold(self, threshold='1.0f'):
        data = '{"transient": {"cluster.routing.allocation.balance.threshold": "%s"}}' % threshold
        self.logger.info('Updating cluster setting: balance_threshold, with data={}'.format(data))
        self.update_cluster_param(self.server, data=data)

    def prep_work(self):
        # Make the balance threshold to 100, so that shards will not relocate (default is 1)
        self.update_balance_threshold(self.server, threshold='100.0f')

    def post_work(self):
        # Make the balance threshold to default
        self.update_balance_threshold(self.server, threshold='1.0f')

    def populate_host_lookup(self):
        try:
            self.logger.debug("Populating hosts for later lookup. From file={}".format(self.options.file_name))
            if self.elected_master is not None:
                master_splitted = self.elected_master.split(".")
                if len(master_splitted) > 1:
                    master_domain = ".".join(master_splitted[1:])
                else:
                    master_domain = ''

            h = {}
            with open(self.options.file_name) as f:
                for i in f.readlines():
                    # self.logger.debug("Reading line " + i)
                    name, ip = i.split(" ")
                    name_splitted = name.split(".")
                    if len(name_splitted) > 1:
                        name_domain = ".".join(name_splitted[1:])
                    else:
                        name_domain = ''

                    if name_domain == master_domain:
                        domain_prefix = ''
                    elif name_domain == '' and master_domain != '':
                        domain_prefix = "." + master_domain
                    else:
                        self.logger.error("Domains do not match. Given in file={}, Cluster configured={}".
                                          format(name_domain, master_domain))
                        # Should we re-map the domain with that of the master?
                        name = name_splitted[:1]
                        domain_prefix = "." + master_domain
                        sys.exit(1)

                    h[name + domain_prefix] = {'host': name, 'fqdn': name + domain_prefix, 'ip': ip}

            # self.logger.debug("Hostname lookup map: {}".format(h))
            return h
        except Exception as e:
            self.logger.error('Something went wrong while reading file or at domain mapping. File="{}", with error="{}'.
                              format(self.options.file_name, e))
            sys.exit(1)

    def setup_logging(self):
        level = logging.INFO
        if self.options.verbose or self.options.debug:
            level = logging.DEBUG

        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                            filename=self.logfile,
                            level=level)

        console = logging.StreamHandler()
        console.setLevel(level=level)
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        console.setFormatter(formatter)

        if self.options.quiet_mode is False:
            logging.getLogger().addHandler(console)

        return logging.getLogger(__name__)

    @classmethod
    def calc_timetaken(cls, node):
        runtime = round(time.time() - cls.start_time, 0)
        cls.logger.info("Finished - {0}. Total time taken in hh:mm:ss is {1}".
                        format(node, str(datetime.timedelta(seconds=runtime))))

    def main(self):
        self.logger.info('Master node is: {}'.format(self.elected_master))
        self.logger.info("Beginning Rolling Restart - have lots of patience! :-)")
        self.wait_for_confirmation()
        hosts_lookup = self.populate_host_lookup()

        try:
            if len(self.options.exclude) == 0:
                excluded_list = self.exclude_default
            else:
                excluded_list = list(self.options.exclude.split(","))

            nodes = self.get_cluster_nodes(excluded_list)

            # Restarts each node, waits to restart next until cluster is green
            num_of_nodes = 0
            for role in self.es_roles:
                num_of_nodes += len(nodes[role])

            # Do any prep work here - updating any settings or so
            # prep_work(options.server)

            for role in self.es_roles:
                for index, node in enumerate(nodes[role], start=1):
                    self.logger.info("=== Restarting {0} of {1} nodes - {2} ===".
                                     format(index, num_of_nodes, node))

                    try:
                        if 'ip' in hosts_lookup[node]:
                            ip = hosts_lookup[node]['ip'].strip()
                            self.logger.debug("Got Ip for %s as %s" % (node, ip))
                        else:
                            self.logger.debug("Could not determine IP for host " + node)
                            print(hosts_lookup)
                    except Exception as e:
                        self.logger.debug("Lookup error, not able to determine IP for host " + node)
                        print(hosts_lookup.keys())
                        sys.exit(1)

                    self.prepare_shutdown(hostname=node, ip=ip)
                    self.wait_for_confirmation()
                    self.check_nodes_up(self.server, count=15)
                    self.shards_allocation_action(self.server, 'disable')
                    # Restart the node here
                    self.restart_es_node(node)
                    self.check_nodes_up(self.server, count=15, wait=180)
                    self.shards_allocation_action(self.server, 'enable')
                    self.get_cluster_state(self.server, wait=600)
                    self.calc_timetaken(node)

        finally:
            # Revert any settings, or confirm final integrity here
            #self.post_work(self.server)
            self.logger.info("Clean up done. Good bye!")


class ArgsPraser(object):
    """
    Handle all arguments parsing here
    """
    def __init__(self):
        self.options = self.setup_args()

        """ Give all commands that you would like to execute on the node that to be restarted. 
            OR Override this cmds by passing a csv arg. Say --remote_cmd 'uptime, service es stop, reboot -f'
        """
        self.remote_cmd = ['df -h',
                           'uname -n',
                           'date',
                           "echo curl -XPOST 'http://localhost:9200/_cluster/nodes/_local/_shutdown'",
                           "service elasticsearch status",
                           "echo reboot -f"
                           ]

        if self.options.remote_cmd is not None:
            self.remote_cmd = list(self.options.remote_cmd.split(","))

        self.options.remote_cmd = self.remote_cmd

    @staticmethod
    def setup_args():
        # Argument Parsing:
        parser = argparse.ArgumentParser(description='Perform rolling restart of Elasticsearch cluster')
        parser.add_argument('-s',
                            '--server',
                            dest='server',
                            action='store',
                            help='Server in ES cluster to communicate with: Example: hostname OR 10.100.2.78',
                            default='localhost')

        parser.add_argument('-e',
                            '--exclude',
                            dest='exclude',
                            action='store',
                            help='Exclude hosts from rolling restart Example: prod-west2-es9,prod-west2-es10',
                            default=[])

        parser.add_argument('-c',
                            '--remote_cmd',
                            dest='remote_cmd',
                            action='store',
                            help='List of commands to be executed on rolling node: uptime,df -h,service es stop,reboot',
                            default=None)

        parser.add_argument('-t',
                            '--test',
                            dest='test',
                            action='store_true',
                            help='Displays hosts that script would be run on, does not perform restart.')

        parser.add_argument('-f',
                            '--file',
                            dest='file_name',
                            action='store',
                            help='File name that contains list of ES nodes in format: "hostname <space> ip".')

        parser.add_argument('-k',
                            '--key_file',
                            dest='ssh_key',
                            action='store',
                            default=os.path.expanduser("~" + '/.ssh/production_key_20180327.pem'),
                            help='SSH key that should be used to logon to boxes.')

        parser.add_argument('-u',
                            '--user',
                            dest='user',
                            action='store',
                            default='ec2-user',
                            help='SSH key that should be used to logon to boxes.')

        parser.add_argument('--dry_run',
                            dest='dry_run',
                            action='store_true',
                            help='Displays most of the runtime info, but do not perform any change/activity.')

        parser.add_argument('-q',
                            '--quite',
                            dest='quiet_mode',
                            action='store_true',
                            help='run in quite mode, no messages on console, but keep all in logfile')

        group_details = parser.add_mutually_exclusive_group()
        group_details.add_argument('-v', '--verbose', action='store_true', help='Print verbose output')
        group_details.add_argument('-d', '--debug', action='store_true', help='run in debug mode')

        return parser.parse_args()


if __name__ == "__main__":
    args = ArgsPraser()
    roller = VeraElasticRoller(server=args.options.server,
                               ssh_key=args.options.ssh_key,
                               user=args.options.user,
                               options=args.options)

    # Call the main function, this does everything!
    roller.main()
