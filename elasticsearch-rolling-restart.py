#!/usr/bin/python

############################################################################################
# This script performs a rolling restart of an Elasticsearch cluster                       #
# based on the following documentation.                                                    #
# https://www.elastic.co/guide/en/elasticsearch/guide/current/_rolling_restarts.html       #
#                                                                                          #
# Run this script on the Saltmaster, since it leverages Salt's service restart ability.    #
############################################################################################

# Source: http://decisionlab.io/blog/2017/02/12/restarting-es

import datetime
import requests
import logging
import json
import sys
import subprocess
import time
import argparse
from getpass import getpass  # Used to request password

# Empty by default to support non-secure clusters.
password = ''

# Track how long we take.
start_time = time.time()

# Set up logging to file
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    filename='cluster_restart-' + time.strftime('%Y_%m_%d_%H_%M' + '.log'),
                    level=logging.INFO)

# Set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

# Set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
console.setFormatter(formatter)

# Add the handler to the root logger
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)

# Relevant Elasticsearch roles.
#
# Note 1: These values appear under the 'roles' field in the response object
#   for _nodes in the api.
#
# Note 2: Order matters here, as we want to restart masters first.
#
# Note 3: Keep an 'other' category because Elastic is liable to add/remove
#   categories on us.
es_roles = ['master' ,'client', 'data', 'other']

# Argument Parsing:
parser = argparse.ArgumentParser(description='Perform rolling restart of Elasticsearch cluster. Must be run on the SaltMaster to restart the cluster.')
parser.add_argument('server',
                    action='store',
                    help='Server in ES cluster to communicate with: Example: hostname OR 192.168.1.0')
parser.add_argument('-e',
                    '--exclude',
                    dest='exclude',
                    action='store',
                    help='Exclude hosts from rolling restart Example: host1.org,host2.org')
parser.add_argument('-u',
                    '--username',
                    dest='user',
                    action='store',
                    help='User name for ES Security, enter password in prompt.')
parser.add_argument('-t',
                    '--test',
                    dest='test',
                    action='store_true',
                    help='Displays hosts that script would be run on, does not perform restart.')

options = parser.parse_args()

# Gets password
if options.user:
    password = getpass()


#############
# Functions #
#############

def do_request(verb, server, auth, verify=False, data=None):
    attempts = 30
    while (attempts > 0):
        try:
            r = requests.request(verb.upper(), server, auth=auth, verify=verify, data=data)

            # Handle HTTP 400 errors, i.e. wrong password.
            if str(r.status_code).startswith('4'):
                logging.error("Request to '{0}' returned HTTP {1}. Are your credentials correct?".format(server, r.status_code))
                exit(1)

            return r
        except requests.exceptions.ConnectionError:
            attempts -= 1
            logging.warn("Attempted connection to {0} failed. Trying {1} more times".format(server, attempts))
            time.sleep(5)


def disable_allocation(server, user, passwd):
    disable = '{"transient": {"cluster.routing.allocation.enable": "none"}}'
    r = do_request(verb = 'put',
                   server = 'http://{0}:9200/_cluster/settings'.format(server),
                   auth = (user, passwd),
                   verify = False,
                   data = disable)
    logging.info("Disabling Allocation: " + r.text)


def enable_allocation(server, user, passwd):
    enable = '{"transient": {"cluster.routing.allocation.enable": "all"}}'
    r = do_request(verb = 'put',
                   server = 'http://{0}:9200/_cluster/settings'.format(server),
                   auth = (user, passwd),
                   verify = False,
                   data = enable)
    logging.info("Enabling Allocation: " + r.text)


def get_cluster_state(server, user, passwd):
    state = "r"

    # Don't return until the cluster is 'green' or 'yellow'
    while True:
        r = do_request(verb = 'get',
                   server = 'http://{0}:9200/_cluster/health'.format(server),
                   auth = (user, passwd),
                   verify = False)
        json_data = json.loads(r.text)
        logging.info("Cluster State: " + json_data["status"])
        state = str(json_data["status"])
        if state == 'yellow' or state == 'green':
            break
        time.sleep(5)

def get_elected_master(server, user, passwd):
    r = do_request(verb = 'get',
                   server = 'http://{0}:9200/_nodes/_master'.format(server),
                   auth = (user, passwd),
                   verify = False)
    json_data = json.loads(r.text)

    # There should only be a single elected master.
    for nodename, values in json_data['nodes'].items():
        master_node = values['name']
    return master_node


def get_cluster_nodes(server, user, passwd, excluded):

    # We will return a dict where each key's value is a list of
    # nodes with a given role (i.e. 'master', 'data', etc...).
    nodelist_len = 0
    nodelist = {}
    for role in es_roles:
        nodelist[role] = []
    logging.info("Requesting node list from cluster")

    r = do_request(verb = 'get',
                   server = 'http://{0}:9200/_nodes'.format(server),
                   auth = (user, passwd),
                   verify = False)
    json_data = json.loads(r.text)

    # Build our dict from the response data.
    for node, values in json_data["nodes"].items():

        # Don't the node if it's in the exclude list.
        if values['name'] in excluded:
            continue

        has_role = False
        for role in es_roles:
            if role in values['roles']:
                has_role = True
                nodelist[role].append(values['name'])
                nodelist_len += 1
                break

        # Node has a role that we're unaware of. Put it in 'other'.
        if not has_role:
            nodelist['other'].append(values['name'])


    # Sort each list of nodes for easier processing and tracking.
    for role in es_roles:
        nodelist[role].sort()

    # We want to restart the Elected Master last, so put its entry
    # at the end of the list of masters.
    elected_master = get_elected_master(server = server, user = user, passwd = passwd)
    elected_master_position = nodelist['master'].index(elected_master)

    # Swap the elected master entry with whatever is currently at the end of the list.
    nodelist['master'][-1], nodelist['master'][elected_master_position] = nodelist['master'][elected_master_position], nodelist['master'][-1]

    logging.info("Obtained list of {0} nodes".format(nodelist_len))
    for role in es_roles:
        logging.info('=== {0} ==='.format(role))
        for node in nodelist[role]:
            logging.info(node)
    return nodelist


def restart_es_node(node):
    # Use Salt to issue a service.restart on elasticsearch.
    logging.info("Restarting ES Node: " + node)
    output = subprocess.Popen(["salt", node, "service.restart", "elasticsearch"],
                              stdout=subprocess.PIPE).communicate()[0]
    logging.info(output)


#########################
# Begin Rolling Restart #
#########################

def main():

    # Assemble list of nodes to exclude if --exclude option is used
    excluded = []
    if options.exclude is not None:
        excluded = options.exclude.split(',')

    if options.test is True:
        get_cluster_nodes(options.server, options.user, password, excluded)
        sys.exit()

    # Begin restart portion
    logging.info("Beginning Rolling Restart")
    nodes = get_cluster_nodes(options.server, options.user, password, excluded)

    # Restarts each node, waits to restart next until cluster is green
    num_of_nodes = 0
    for role in es_roles:
        num_of_nodes += len(nodes[role])

    for role in es_roles:
        for index, node in enumerate(nodes[role], start = 1):
            logging.info("Restarting {0} of {1} nodes".format(index, num_of_nodes))
            disable_allocation(options.server, options.user, password)
            restart_es_node(node)
            enable_allocation(options.server, options.user, password)
            get_cluster_state(options.server, options.user, password)

    runtime = round(time.time() - start_time, 0)
    logging.info("Finished. Total time in hh:mm:ss is {0}".format(str(datetime.timedelta(seconds=runtime))))


if __name__ == "__main__":
    main()
