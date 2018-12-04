#!/usr/bin/python3
"""
Author      :   Vivek KC
Email       :   devops@Org.com
Date        :   Tue Aug 28 00:27:54 IST 2018

Description :   This script is to automate branch cut for Sprints at Org.

                Declare all the repository details in repo.conf file. That's loaded as dependency

"""
import os
import sys
import time

from configparser import ConfigParser
from functools import wraps
import logging
import argparse
import getpass
import subprocess
from subprocess import PIPE
from sh import git
import sh
import re
import shlex
import shutil

# from pathlib import Path

from git import (
    Repo,
    Git)


def setup_logging(opts=None):
    level = logging.INFO
    if opts.verbose or opts.debug:
        level = logging.DEBUG

    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        filename=logfile,
                        level=level)

    console = logging.StreamHandler()
    console.setLevel(level=level)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    console.setFormatter(formatter)

    if opts.quiet_mode is False:
        logging.getLogger().addHandler(console)

    return logging.getLogger(__name__)


def args_extractor():
    parser = argparse.ArgumentParser(description="Branch Cut automation script for Org Bitbucket repositories")
    parser.add_argument('-j',
                        '--jump-box',
                        dest='server',
                        action='store',
                        help='Devops jump server. Example: hostname OR 10.0.1.18',
                        default='localhost')

    parser.add_argument('-e',
                        '--exclude',
                        dest='excluded_repos',
                        action='store',
                        help='Exclude repos on the fly. '
                             'Pass a csv such as: "server, view-in-browser" or "ALL" if you should exclude all repos',
                        default='None')

    parser.add_argument('-r',
                        '--repo-list',
                        dest='included_repos',
                        action='store',
                        help='Do these repos even if disabled in repo.conf (and exclude all others not in provided) '
                             'Pass a csv such as: "server, view-in-browser" or "ALL" if you should include all repos.',
                        default='')

    parser.add_argument('-f',
                        '--file',
                        dest='conf_file',
                        action='store',
                        default=None,
                        help='File path that contains details about the repositories')

    parser.add_argument('-t',
                        '--test-run',
                        dest='is_testrun',
                        action='store_true',
                        default=False,
                        help='Do a test run using a candidate test repo. Exclude all prod repos')

    parser.add_argument('-s',
                        '-i',
                        '--sprint',
                        dest='Org_sprint',
                        action='store',
                        type=int,
                        required=True,
                        help='Current Org Sprint or Iteration for which Branch cut to be done. Say 120, 121, etc')

    parser.add_argument('-k',
                        '--key-file',
                        dest='ssh_key',
                        action='store',
                        default=os.path.expanduser("~" + '/.ssh/production_key_20180327.pem'),
                        help='SSH key that should be used to logon to remote boxes')

    parser.add_argument('-u',
                        '--user',
                        dest='user',
                        action='store',
                        default='ec2-user',
                        help='Remote user that logon to boxes.')

    parser.add_argument('--wet-run',
                        dest='wet_run',
                        action='store_true',
                        default=False,
                        help='Displays most of the runtime info, but do not perform any change/activity.')

    parser.add_argument('--force',
                        dest='force_run',
                        action='store_true',
                        default=False,
                        help='Force every run without waiting for user input/confirmation. Do at your risk!')

    parser.add_argument('-q',
                        '--quite',
                        dest='quiet_mode',
                        action='store_true',
                        help='run in quite mode, no messages on console, but keep all in logfile')

    parser.add_argument('-b',
                        '--base-dir',
                        dest='base_dir',
                        action='store',
                        default=os.getcwd(),
                        help='Directory where the remote repo should be checked out, looked for..')

    parser.add_argument('-P',
                        '--update-pom',
                        dest='is_update_pom',
                        action='store_true',
                        default=False,
                        help='Should we update the POM files in server repo with the MAJOR.MINOR.ITERATION')

    parser.add_argument('-V',
                        '--version-number',
                        dest='pom_version_num',
                        action='store',
                        default=None,
                        help='Pass a valid POM version in the form: MAJOR.MINOR \
                        (Iteration will be auto-populated based on the sprint argument/branch name)')

    parser.add_argument('-T',
                        '--jira-ticket',
                        dest='jira_ticket',
                        action='store',
                        default='DEVOP-3281',
                        help='Give a valid Org/DEVOPs ticket thats used for tracking this change request')

    group_details = parser.add_mutually_exclusive_group()
    group_details.add_argument('-v', '--verbose', action='store_true', help='Print verbose output')
    group_details.add_argument('-d', '--debug', action='store_true', help='run in debug mode')

    return parser.parse_args()


class Decorators(object):
    """
    Write all the external functionality here and decorate original functions for easy reading
    """
    def __init__(self, opts=None):
        self.options = opts

    @classmethod
    def bitbucket_authenticate(cls, func=None):
        def wrapper(*args, **kwargs):
            logger.debug("Placeholder for Bitbucket authentication! For now pass!")
            if cls.get_token() is True:
                return func(*args, **kwargs)
            else:
                logger.error("Bitbucket token error, authentication failed!")
                sys.exit(1)
        return wrapper

    @classmethod
    def get_token(cls):
        return True

    @classmethod
    def skip_dryrun(cls, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if options.wet_run is False:
                logger.info('Call: function={}, args={}, kwargs={}'.format(func.__name__, args[1:], kwargs))
                logger.info("Dry run, skipped execution! When ready, re-run with argument --wet-run")
                return False, False
            else:
                return func(*args, **kwargs)

        return wrapper


class MergeError(Exception):
    pass


class ExitOnError(Exception):
    pass


class OrgBranchCut(object):
    """
    Create a new branch from master and commit to git/remote
    """
    def __init__(self, opts=None, log=None, base_dir=None):
        self.options = opts
        self.logger = log
        self.iteration = self.options.Org_sprint
        self.base_dir = base_dir
        self.user = getpass.getuser()
        self.iteration_previous = self.iteration - 1
        # self.excluded_repo = False
        self.merge_previous_branch = False
        self.is_testrun = self.options.is_testrun
        self.jira_ticket = self.options.jira_ticket

        # POM version for server repo. These variables are sourced from Jenkins/ENV vars, or by args
        self.major_number = None
        self.minor_number = None
        self.iteration_notused = None
        self.update_version_numbers(version_string=self.options.pom_version_num)

        # Manage repo inclusion/exclusion
        self.args_excluded_repos = self.options.excluded_repos.split(",")
        self.args_included_repos = self.options.included_repos.split(",")

        self.summary_data = []

        if self.base_dir is None:
            self.base_dir = self.options.base_dir

        if not os.path.isdir(self.base_dir):
            self.logger.debug("Base directory - {} is not found, create it first?".format(self.base_dir))
            os.makedirs(self.base_dir)

        assert(os.path.isdir(self.base_dir))

        self.git_ssh_identity_file = self.options.ssh_key
        self.git_ssh_cmd = 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i {}'. \
            format(self.git_ssh_identity_file)

        if self.options.conf_file is None:
            self.conf_file = os.path.dirname(os.path.realpath(__file__)) + '/' + 'repo.conf'
        else:
            self.conf_file = self.options.conf_file

        self.logger.info("Beginning Branch CUT for Org Sprint# " + str(self.iteration))
        self.repo_path = None
        self.pom_update_script = './scripts/updateProjectVersion.sh'

    def __repr__(self):
        return '{}={}'.format(self.__class__.__name__, self.iteration)

    def git_remote_clone(self, repo_url=None, path='/tmp/branch_cut', branch='master'):
        with Git().custom_environment(GIT_SSH_COMMAND=self.git_ssh_cmd):
            Repo.clone_from(repo_url, path, branch)

    def update_version_numbers(self, version_string=None):
        if self.options.is_update_pom:
            if version_string is not None:
                self.major_number, self.minor_number = version_string.split('.')
            else:
                try:
                    """ 
                    POM version for server repo. These variables are sourced from Jenkins.
                    Declare + Export these if you are running locally
                    """
                    self.major_number = os.environ['TEST1_MAJOR']
                    self.minor_number = os.environ['TEST1_MINOR']
                    self.logger.warn('You better pass a POM version explicitly by: -V MAJOR.MINOR')

                    # Not used because we will look for the SPRINT/ITERATION number passed with arg -s
                    #self.iteration = os.environ['TEST1_ITERATION']
                except NameError as e:
                    self.logger.error('Not Jenkins? Then go export TEST1_MAJOR, TEST1_MINOR before calling this script')
                    sys.exit(1)
                except Exception as e:
                    self.logger.error('Something wrong with dealing with MAJOR and MINOR numbers, bailing on: {}'.
                                      format(e))
                    sys.exit(1)

            if self.major_number is None or self.minor_number is None:
                self.logger.error('Something wrong with determining MAJOR and MINOR numbers, bailing!')
                sys.exit(1)
        else:
            self.logger.info('POM files/version update will not be done by this run. If you care, pass -P')

    def exec_git_commit(self, branch='master', msg='Committing the changes by automation'):
        """ This does whatever it takes to push the changes to git remote repo """
        git_cmds = list()
        git_cmds.append(['git', 'add', '.'])
        git_cmds.append(['git', 'commit', '-m', msg])
        git_cmds.append(['git', 'push', 'origin', branch])

        for index, cmd in enumerate(git_cmds):
            self.logger.info('Commit step {} - going to exec: {}'.format(index, cmd))
            try:
                stdout, stderr = self.git_command_run(git_cmd=cmd, repo_path=self.repo_path)
            except Exception as e:
                self.logger.error("Something went wrong at git commit & remote push! Error: {}".format(e))
                sys.exit(1)
        return True

    def git_merge(self, base_branch='development', merge_branch='master', repo_name='None', *args, **kwargs):
        # cmd = 'git merge --no-ff merge_branch'
        try:
            do_push = False
            self.logger.info('Action: checkout base branch "{}", and then merge "{}" into it'.
                             format(base_branch, merge_branch))
            self.checkout_gitbranch(repo_path=self.repo_path, branch_name=base_branch, is_new_branch=False)

            # Merge command
            git_cmd = ['git', 'merge', merge_branch, '--no-ff', '--no-edit']
            self.logger.debug('Merge action to be run is --> [on {}]: {}'.format(base_branch, git_cmd))
            stdout_cb, stderr_cb = self.git_command_run(git_cmd=git_cmd, repo_path=self.repo_path)

            if stdout_cb is not False and stderr_cb is not False:
                if str(stdout_cb).find("Merge made by the 'recursive' strategy") > 0:
                    self.logger.info("Merge operation is successful locally")
                    do_push = True
                elif str(stdout_cb).find("Already up to date.") > 0 or \
                        str(stdout_cb).find("Already up-to-date.") > 0:
                    self.logger.info("Merge is not required, it's up to date already!")
                    return True
                elif str(stderr_cb).find("merge: {} - not something we can merge".format(merge_branch)) > 0 or \
                        str(stderr_cb).find("fatal: {} - not something we can merge".format(merge_branch)) > 0:
                    self.logger.error("Merge could not be done for branches: {} ==> {}! You got to do this manually!!"
                                      .format(merge_branch, base_branch))
                else:
                    self.logger.error("Merge is NOT successful for {}! Error: {}".format(base_branch, stderr_cb))

            if do_push:
                return self.pushout_gitbranch(repo_name=repo_name, branch_name=base_branch)

        except Exception as e:
            self.logger.error("Something went wrong at repo branch merge! Error: {}".format(e))
            sys.exit(1)

    def skip_if_excluded(self, repo_data=None):
        if repo_data is not None:
            reason = ""
            comment = ""
            ret_val = True
            self.logger.debug('Checking if this repo should be excluded..')
            if repo_data['repo_name'] in self.args_included_repos or 'ALL' in self.args_included_repos:
                    # Enabled this repo on the fly. Disable rest of the repos not on this list
                    ret_val = False
                    reason = "This repo is enabled on the fly by user will"
                    comment = "User forced to run"
            else:
                if repo_data['repo_name'] in self.args_excluded_repos or 'ALL' in self.args_excluded_repos:
                    reason = 'This repo is excluded on the fly by the user'
                    comment = "Skipped by exclude argument"
                else:
                    if 'excluded' in repo_data and repo_data['excluded'] is True:
                        reason = 'This repo is excluded by config, with reason="{}"'. \
                            format(repo_data.get('excluded_reason', 'NA'))
                        comment = "Skipped excluded repo"
                    elif self.is_testrun:
                        reason = 'Prod repo {} is skipped as this is a test run!'.format(repo_data['repo_name'])
                        comment = "Skipped prod repo on test run"
                    # elif not repo_data['repo_name'] == 'devops-test':
                    #     reason = 'Prod repo {} is skipped. Remove this check when ready for rollout!'.\
                    #                 format(repo_data['repo_name'])
                    #     comment = 'Skipped PROD'
                    else:
                        # Finally after all these check, repo not excluded, go for it!!
                        ret_val = False

            return ret_val, reason, comment

    def update_summary_table(self, data=None):
        if data:
            self.summary_data.append("=" * 50)
            self.summary_data.append(data)

    @Decorators.bitbucket_authenticate
    def main(self):
        repo_data = self.load_repo_data

        repos = dict(repo_data.items('repositories'))
        default = dict(repo_data.items('default'))

        count = 0
        for repo in repos:
            repo_kwargs = eval(repos[repo])
            count += 1

            if 'branch_pattern' in repo_kwargs:
                repo_kwargs['new_branch'] = repo_kwargs['branch_pattern'] + str(self.iteration)
            else:
                repo_kwargs['new_branch'] = '{pattern}{iteration}'.format(pattern=eval(default['branch_pattern']),
                                                                          iteration=self.iteration)
            repo_path = self.base_dir + '/' + repo
            self.repo_path = repo_path

            if 'from_branch' not in repo_kwargs:
                repo_kwargs['from_branch'] = eval(default['from_branch'])

            if 'merge_previous_branch' in repo_kwargs:
                self.merge_previous_branch = repo_kwargs['merge_previous_branch']
            else:
                self.merge_previous_branch = default['merge_previous_branch']

            self.formatter(string='#', count=72, align_left=True)
            self.logger.info('({}) Processing repo "{}" ---'.format(count, repo))
            self.logger.debug('Repo details: {}'.format(repo_kwargs))

            ret_val, reason, comment = self.skip_if_excluded(repo_data=repo_kwargs)
            if ret_val:
                self.logger.warn(reason)
                self.update_summary_table(data='{}. repo={} | status={}'.format(count, repo, comment))
                continue
            else:
                self.logger.info('Repo is not excluded, proceeding..')

            git_cmd = 'git pull'
            action = 'pull'
            if self.check_if_gitrepo(repo_path=repo_path):
                self.logger.info("It's active locally.. so will just pull from remote")
                # Make sure the local copy is clean..
                self.logger.info("Making sure the local copy is clean, resetting all uncommitted changes if any!")
                self.exec_command(cmd=['git', 'reset', '--hard', 'HEAD'], path=self.repo_path)
            else:
                self.logger.info('Repo is not active locally.. will clone freshly from remote')
                git_cmd = 'git clone {}'.format(repo_kwargs['repo_url'])
                action = 'clone'
                # should you clean up checkout repo/directory if not empty? Mostly no!
                #shutil.rmtree(repo_path)
                repo_path = self.base_dir

            # Do repo clone or pull
            stdout, stderr = self.git_command_run(git_cmd=shlex.split(git_cmd), repo_path=repo_path)
            if stdout is not False and stderr is not False:
                if str(stderr).find("Cloning into '{}'".format(repo)) > 0 or \
                        str(stdout).find("Cloning into '{}'".format(repo)) > 0:
                    self.logger.info("Cloning completed")
                elif str(stdout).find("Already up to date") > 0 or \
                        str(stdout).find("Already up-to-date") > 0 or \
                        str(stderr).find("Already up to date") > 0:
                    self.logger.info("Completed {} successfully, it's up to date!".format(action))
                else:
                    self.logger.error("Remote {} is NOT successful! Error: {}".format(action, stderr))
                    self.update_summary_table(data='{}. repo={} | status=Failed at repo {}'.
                                              format(count, repo, action))
                    continue

            """
            Merge if need be. Say, merge previous iteration branch into both master and development, and then create
            a new branch from development.
            """
            self.formatter()
            if self.merge_previous_branch is True and repo_kwargs['merge_to_branches']:
                self.logger.info('Merge to branch is enabled, doing it here for {}'.
                                 format(repo_kwargs['merge_to_branches']))
                global merge_error
                merge_error = False
                previous_iteration_branch = repo_kwargs['branch_pattern'] + str(self.iteration_previous)

                """
                If you don't checkout the previous iteration branch locally, the merge fails
                """
                self.logger.debug('Checking out previous iteration branch "{}"'.format(previous_iteration_branch))
                self.checkout_gitbranch(repo_path=self.repo_path,
                                        branch_name=previous_iteration_branch, is_new_branch=False)

                # Do a pull and ensure you have all updated locally
                stdout, stderr = self.git_command_run(git_cmd=['git', 'pull', 'origin', previous_iteration_branch],
                                                      repo_path=self.repo_path)

                for merge_to_branch in repo_kwargs['merge_to_branches']:
                    print("")
                    self.logger.info('Processing for merging branch - {} with previous iteration branch {}'.
                                     format(merge_to_branch, previous_iteration_branch))
                    merge_out = self.git_merge(base_branch=merge_to_branch,
                                               merge_branch=previous_iteration_branch, **repo_kwargs)
                    if not merge_out:
                        if self.options.wet_run is True:
                            self.logger.error('Can not proceed on merge error, skipping this repo..')
                            self.update_summary_table(data='{}. repo={} | status=Skipped on Merge error at {}'.
                                                      format(count, repo, merge_to_branch))
                            merge_error = True
                            break
                        else:
                            # self.update_summary_table(data='{}. repo={} | status=Skipped on dry-run'.
                            #                           format(count, repo, merge_to_branch))
                            pass
                if merge_error:
                    continue
            else:
                self.logger.info('Merge to branch is not specified, moving on..')

            # break
            comment = 'FAILED!!!'
            if self.cut_new_branch(**repo_kwargs):
                if self.options.wet_run:
                    comment = 'Successful!'
                else:
                    comment = 'Dry-run skipped execution!'

                self.formatter()
                # If server repository, update pom.xml to match with MAJOR.MINOR.ITERATION
                self.logger.info('Checking if POM files to be updated..')
                if repo == 'server' or repo == 'devops-test':
                    if self.options.is_update_pom and repo_kwargs['pom_branches']:
                        if 'pom_update_script' in repo_kwargs:
                            pom_update_script = repo_kwargs['pom_update_script']
                        else:
                            pom_update_script = self.pom_update_script

                        for branch in repo_kwargs['pom_branches']:
                            """ If branch is master, POM version has to be current sprint/iteration + 1 """
                            if branch == 'master':
                                iteration_local = self.iteration + 1
                            elif branch == 'current_sprint_branch':
                                iteration_local = self.iteration
                                branch = repo_kwargs['new_branch']

                                self.logger.info('We are not updating POM files for current branch {}.\
                                This would assume previous master version'.format(branch))
                                continue

                            self.logger.info('Processing POM updates for branch={}'.format(branch))

                            pom_version = '{}.{}.{}'.format(self.major_number, self.minor_number, iteration_local)
                            self.update_pom_version(repo=repo, version=pom_version,
                                                    pom_update_script=pom_update_script,
                                                    branch=branch)
                    else:
                        self.logger.info('Updating the server POMs skipped..')
                else:
                    self.logger.debug('POM files update not required for {}..'.format(repo))

                # Show some logs
                self.formatter(align_left=False)
                self.show_commit_logs(repo=repo, repo_path=repo_path)

            self.update_summary_table(data='{}. repo={} | status={}'.format(count, repo, comment))

        '''
        ########################### END ##################################
        
        This is end of the run - let's print a summary for quick reference
        
        '''
        print("\n\n")
        self.logger.info('+++++++ Here is the summary of execution +++++++')
        self.print_summary

        '''

        ## End of main()
        
        All should be done by now. Good Bye!
        
        '''

    @property
    def print_summary(self):
        # Print Summary
        print("\n")
        for raw in self.summary_data:
            self.logger.info(raw)

        self.formatter(string='=', align_left=True, count=50)

    def show_commit_logs(self, repo, repo_path):
        # Repo object used to programmatically interact with Git repositories
        self.logger.debug("Showing some recent commit logs, ensure all you see is good & expected!")
        if not os.path.isdir(repo_path) and self.options.wet_run is True:
            self.logger.error('Could not locate repo directory {}, please checkout/create it!'.format(repo_path))
            return

        if self.check_if_gitrepo(repo_path=self.repo_path):
            try:
                r = Repo(self.repo_path)
                # check that the repository loaded correctly
                if not r.bare:
                    self.logger.debug('Repo at {}/{} successfully loaded.'.format(self.base_dir, repo))
                    self.print_repository(r)
                    # create list of commits then print some of them to stdout
                    commits = list(r.iter_commits('master'))[:COMMITS_TO_PRINT]
                    for commit in commits:
                        self.print_commit(commit)
                        pass

                    print("\n\n")
                    self.logger.warn('Attention: You see these commits? Are they matching and you sure its good to go?')
                    print('^^ END <<<%%%%%%%%%%%%%%>>>\n\n')
                else:
                    self.logger.error('Could not load repository at {} :('.format(self.base_dir))
            except Exception as e:
                self.logger.error('Could not load repository at {}, error: {}'.format(repo_path, e))
                raise ExitOnError
        elif self.options.wet_run is False:
            self.logger.info('Repo not found locally, ignoring on the dry-run..')
        else:
            self.logger.error('Not a valid repo {}, can not show commit logs!'.format(self.repo_path))
            return

    # @staticmethod
    def formatter(self, string='-', count=30, align_left=False):
        if align_left:
            self.logger.info(string * count)
        else:
            self.logger.info("\t\t\t" + string * count)

    @staticmethod
    def update_gitsettings(repo_name=None):
        git_config = subprocess.call(['git', 'config', 'core.autocrlf', 'true'], cwd=repo_name, stdout=PIPE,
                                     stderr=PIPE, shell=True)

    def fetch_repo_changes(self, repo_name=None):
        git_fetch = subprocess.Popen(['git', 'fetch'], cwd=repo_name, stdout=PIPE, stderr=PIPE, shell=True)
        stdout_f, stderr_f = git_fetch.communicate()
        self.logger.debug(stdout_f)
        self.logger.debug(stderr_f)

    def pull_repo_changes(self, repo_name=None):
        git_pull = subprocess.call(['git', 'pull'], cwd=repo_name, stdout=PIPE, stderr=PIPE, shell=True)

        if git_pull != 0:
            self.logger.debug("GIT PULL didn't succeed, check your git status.")
        else:
            self.logger.debug("GIT PULL ended successfully.")

        return True

    def check_if_gitrepo(self, repo_path):
        return os.path.isdir(repo_path + '/.git')

    @property
    def check_wetrun(self):
        if self.options.wet_run is True:
            return True
        else:
            return False

    @property
    def check_dryrun(self):
        if self.options.wet_run is False:
            self.logger.info("Dry-run, skipped exec..")
            return True
        else:
            return False

    @Decorators.skip_dryrun
    def git_command_run(self, git_cmd=[], repo_path=None):
        try:
            self.logger.info('Running git command: {}'.format(git_cmd))
            if self.options.force_run is False:
                # return False, False
                # TBD: Disable prompting for confirmation, and let script run auto
                pass

            """
            Sample git_cmd format
             # git_cmd = ['git', 'clone', 'git@bitbucket.org:Orgdocs/rpm-Orgbase.git']
             # git_cmd = ['git remote -v']
            """
            git_run = subprocess.Popen(git_cmd, cwd=repo_path, stdout=PIPE, stderr=PIPE)
            stdout, stderr = git_run.communicate()
            self.logger.debug('For troubleshooting --> Out is: {}, Error is: {}'.format(stdout, stderr))
            return stdout, stderr
        except Exception as e:
            self.logger.error('Could not run git command: {}. Error is: {}'.format(git_cmd, e))
            raise

    @Decorators.skip_dryrun
    def exec_command(self, cmd=[], path=None):
        if path is None:
            path = self.repo_path

        try:
            self.logger.info('Running shell command: {}'.format(cmd))
            if self.options.force_run is True:
                # TBD - disable prompting
                self.logger.debug('Disabled prompting, assume Yes to all user inputs/confirm.')
                pass

            cmd_run = subprocess.Popen(cmd, cwd=path, stdout=PIPE, stderr=PIPE)
            stdout, stderr = cmd_run.communicate()
            self.logger.debug('For troubleshooting --> Out is: {}, Error is: {}'.format(stdout, stderr))
            return stdout, stderr
        except Exception as e:
            self.logger.error('Could not run: {}. Error is: {}'.format(cmd_run, e))
            raise

    def update_pom_version(self, repo=None, version=None, branch='master', pom_update_script=None):
        """
        From Jenkins get ==> args='${MAJOR}.${MINOR}.${ITERATION_SPRINT}'
        Update the pom.xml on server repo for below branches 
            - master : MAJOR.MINOR.ITERATION+1
            
            # You may not update the POM on the newly cut branch as it should follow what's in the master (already set)
            - new branch : MAJOR.MINOR.ITERATION
        """
        src_path = self.repo_path
        if repo == 'devops-test':
            src_path = self.repo_path + '/server'

        cmd = [pom_update_script, version]
        if version is not None:
            stdout, stderr = self.git_command_run(git_cmd=['git', 'checkout', branch], repo_path=self.repo_path)
            self.logger.info('Updating the server POMs as {}'.format(version))
            stdout, stderr = self.exec_command(cmd=cmd, path=src_path)
            if str(stdout).find('BUILD SUCCESS') > 0 or str(stderr).find('BUILD SUCCESS') > 0:
                self.logger.info('Updated POM files.. you could commit now!')

                """ This does git add, commit and remote push out """
                self.exec_git_commit(branch=branch,
                                     msg='{}: Branch cut automation - POM files on {} updated as {} for SPRINT # {}'.
                                     format(self.jira_ticket, branch, version, self.iteration)
                                     )
            else:
                self.logger.error('Failed to update POM files.. aborting all local changes..!')
                self.exec_command(cmd=['git', 'reset', '--hard', 'HEAD'], repo_path=self.repo_path)
        else:
            self.logger.debug('No POM version was passed as MAJOR.MINOR, skipping the update..')

    def checkout_gitbranch(self, repo_name=None, branch_name=None, is_new_branch=False, repo_path=None):
        git_cmd = ['git', 'checkout', branch_name]
        if is_new_branch is True:
            git_cmd = ['git', 'checkout', '-b', branch_name]

        try:
            stdout_cb, stderr_cb = self.git_command_run(git_cmd=git_cmd, repo_path=repo_path)
            if stdout_cb is not False and stderr_cb is not False:
                if is_new_branch:
                    if str(stderr_cb).find("fatal: A branch named " + "'" + branch_name + "'" + " already exists.") > 0:
                        self.logger.error('Could not create "{}" branch, there is already one!'.
                                          format(branch_name))
                        return False
                    elif str(stderr_cb).find("Switched to a new branch '{}'".format(branch_name)) > 0:
                        self.logger.info('Created the new branch "{}" locally and checked out!'.format(branch_name))
                        return True
                    else:
                        # TBD: What other condition to check here?
                        return False
                else:
                    if str(stdout_cb).find("Your branch is up to date with 'origin/{}'".format(branch_name)) > 0 or \
                            str(stderr_cb).find("Already on '{}'".format(branch_name)) > 0 or \
                            str(stdout_cb).find("Branch {} set up to track remote branch {}".
                                                        format(branch_name, branch_name)) > 0 or \
                            str(stdout_cb).find("Branch '{}' set up to track remote branch '{}'".
                                                        format(branch_name, branch_name)) > 0:

                        self.logger.debug('Checked out "{}" branch successfully.'.format(branch_name))
                        return True
                    else:
                        self.logger.error('Failed to checked out "{}" branch.'.format(branch_name))
                        return False
        except Exception as e:
            self.logger.error("Something went wrong at branch create/checkout! Error: {}". format(e))
            sys.exit(1)
        # finally:
        #     self.logger.debug("Putting you back home - " + self.base_dir)
        #     os.chdir(self.base_dir)

    def get_current_branch(self):
        try:
            status = str(git("status"))
        except sh.ErrorReturnCode as e:
            raise RuntimeError(e.stderr.decode())

        match = re.match("On branch (\w+)", status)
        current = match.group(1)

        self.logger.info("In {curr} branch".format(curr=current))

        if status.endswith("nothing to commit, working directory clean\n"):
            self.logger.debug("Directory clean in {} branch".format(current))
        else:
            raise MergerError("Directory not clean, must commit:\n"
                              "{status}".format(status=status))
        return current

    def pushout_gitbranch(self, repo_name=None, branch_name=None, remote='origin', *args, **kwargs):
        if repo_name is None:
            self.logger.error("a repo_name is mandatory for remote pushout!")
            return False
        try:
            git_cmd = ['git', 'push', '--set-upstream', remote, branch_name]
            self.logger.debug('Remote push: {}'.format(git_cmd))
            stdout_cb, stderr_cb = self.git_command_run(git_cmd=git_cmd, repo_path=self.repo_path)

            if stdout_cb is not False and stderr_cb is not False:
                find_str = "Branch '{}' set up to track remote branch '{}' from '{}'".format(branch_name, branch_name, remote)
                self.logger.debug("Search string is: " + find_str)
                if str(stdout_cb).find(find_str) > 0:
                    self.logger.debug("Remote push out is successful")
                    return True
                elif str(stdout_cb).find("Branch {} set up to track remote branch {} from origin".
                                                 format(branch_name, branch_name, remote)) > 0 or \
                        str(stderr_cb).find("Everything up") > 0:
                    self.logger.debug("All up to date..")
                    return True
                else:
                    self.logger.debug("Remote push out is NOT successful - check!")
                    return False
        except Exception as e:
            self.logger.error("Something went wrong repo remote pushout! Error: {}".format(e))
            sys.exit(1)


    @staticmethod
    def print_commit(commit):
        print('----')
        print(str(commit.hexsha))
        print("\"{}\" by {} ({})".format(commit.summary,
                                         commit.author.name,
                                         commit.author.email))
        print(str(commit.authored_datetime))
        print(str("count: {} and size: {}".format(commit.count(),
                                                  commit.size)))

    def print_repository(self, repo):
        self.logger.info('Repo description: {}'.format(repo.description))
        self.logger.info('Repo active branch is {}'.format(repo.active_branch))
        for remote in repo.remotes:
            self.logger.info('Remote named "{}" with URL "{}"'.format(remote, remote.url))
        self.logger.info('Last commit for repo is {}.'.format(str(repo.head.commit.hexsha)))

    @Decorators.skip_dryrun
    def cut_new_branch(self, repo_name=None, new_branch=None, from_branch=None, *args, **kwargs):

        """ This is the main section where branch cut is done """

        try:
            self.formatter()
            # self.logger.debug('New Branch name is: {}'.format(new_branch))
            self.logger.info('Going to cut a new branch for repo="{}", from_branch="{}", new_branch="{}"'.
                             format(repo_name, from_branch, new_branch))
            # Check out the from branch - say master
            self.logger.debug('Checking out the base branch "{}", from which the new branch to be cut'.
                              format(from_branch))
            self.checkout_gitbranch(repo_path=self.repo_path, branch_name=from_branch, is_new_branch=False)

            # Now create a new branch from checked out branch, say from master
            self.logger.debug('Checking out to the new branch "{}", it gets created here..'.
                              format(new_branch))

            out = self.checkout_gitbranch(repo_path=self.repo_path, branch_name=new_branch, is_new_branch=True)
            if not out:
                self.logger.error('Skipping on new branch checkout failure..')
                return False

            time.sleep(1)
            return self.pushout_gitbranch(repo_name=repo_name, branch_name=new_branch)
        except Exception as e:
            raise RuntimeError("Something went wrong with the arguments? Err={}".format(e))
            sys.exit(1)

    @property
    def load_repo_data(self):
        self.logger.debug("Loading repo conf from: " + self.conf_file)
        try:
            if os.path.isfile(self.conf_file) is not True:
                raise IOError
            repo_config = ConfigParser()
            repo_config.read(self.conf_file)
            self.logger.debug('Sections found in repo config parser: ' + str(repo_config.sections()))
        except IOError:
            self.logger.error('repo conf file - {} not found!'.format(self.conf_file))
            sys.exit(1)
        except Exception as e:
            self.logger.error('Could not safe load repo conf. Error: {}'.format(e))
            sys.exit(1)

        return repo_config


class OrgNewBranch(OrgBranchCut):

    def __init__(self, repo_name, repo_url, checkout_branch, new_branchname, *args, **kwargs):
        self.repo_name = repo_name
        self.repo_url = repo_url
        self.checkout_branch = checkout_branch
        self.new_branchname = new_branchname
        self.args = args
        self.kwargs = kwargs


if __name__ == "__main__":

    if sys.version_info[0] < 3:
        print("Hey, sorry this script is compatible with python-3.x only :-(")
        sys.exit(1)

    logfile = 'Org-branchcut' + time.strftime('%Y_%m_%d_%H_%M' + '.log')
    options = args_extractor()
    logger = setup_logging(opts=options)

    COMMITS_TO_PRINT = 2
    vbc = OrgBranchCut(opts=options, log=logger)
    vbc.main()

    sys.exit(0)
