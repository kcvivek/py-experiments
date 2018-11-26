#!/usr/bin/python3
"""
Author      : Vivek KC
Email       : devops@vera.com
Date        : Tue Aug 28 00:27:54 IST 2018

Description : This script is to automate branch cut for Sprints

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
    parser = argparse.ArgumentParser(description="Branch Cut automation script for Vera Bitbucket repositories")
    parser.add_argument('-s',
                        '--server',
                        dest='server',
                        action='store',
                        help='Devops jump server. Example: hostname OR 10.0.1.18',
                        default='localhost')

    parser.add_argument('-e',
                        '--exclude',
                        dest='exclude',
                        action='store',
                        help='Exclude hosts from rolling restart Example: prod-west2-es9,prod-west2-es10',
                        default=[])

    parser.add_argument('-f',
                        '--file',
                        dest='file_name',
                        action='store',
                        help='File name that contains list of ES nodes in format: "hostname <space> ip".')

    parser.add_argument('-k',
                        '--key-file',
                        dest='ssh_key',
                        action='store',
                        default=os.path.expanduser("~" + '/.ssh/production_key_20180327.pem'),
                        help='SSH key that should be used to logon to boxes.')

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
                        help='run in quite mode, no messages on console, but keep all in logfile')

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


class VeraBranchCut(object):
    """
    Create a new branch from master and commit to git/remote
    """
    def __init__(self, opts=None, log=None, base_dir=None, iteration=120):
        self.options = opts
        self.logger = log
        self.iteration = iteration
        self.base_dir = base_dir
        self.user = getpass.getuser()

        if self.base_dir is None:
            self.base_dir = self.options.base_dir

        self.git_ssh_identity_file = self.options.ssh_key
        self.git_ssh_cmd = 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i {}'.\
            format(self.git_ssh_identity_file)

        self.logger.info("Beginning Branch CUT for Vera Sprint# " + str(self.iteration))

    def __repr__(self):
        return '{}={}'.format(self.__class__.__name__, self.iteration)

    def git_remote_clone(self, repo_url=None, path='/tmp/kc123', branch='master'):
        with Git().custom_environment(GIT_SSH_COMMAND=self.git_ssh_cmd):
            Repo.clone_from(repo_url, path, branch)

    def git_commit(self):
        pass

    def git_merge(self):
        pass

    @Decorators.bitbucket_authenticate
    def main(self):
        repo_data = self.load_repo_data()

        repos = dict(repo_data.items('repositories'))
        default = dict(repo_data.items('default'))

        count = 0
        for repo in repos:
            repo_kwargs = eval(repos[repo])
            count += 1

            if count > 2:
                break

            if 'new_branchpattern' in repo_kwargs:
                repo_kwargs['new_branch'] = repo_kwargs['new_branchpattern'] + str(self.iteration)
            else:
                repo_kwargs['new_branch'] = '{pattern}{iteration}'.format(pattern=eval(default['new_branchpattern']),
                                                                          iteration=self.iteration)

            if 'from_branch' not in repo_kwargs:
                repo_kwargs['from_branch'] = eval(default['from_branch'])

            self.logger.info('=========== ({}) Processing repo "{}" ==========='.format(count, repo))

            self.git_command_run(git_cmd=list('git clone {}'.format('url').split()))

            self.cut_new_branch(**repo_kwargs)

            # Repo object used to programmatically interact with Git repositories
            r = Repo(self.base_dir + '/' + repo)
            # check that the repository loaded correctly
            if not r.bare:
                logger.debug('Repo at {}/{} successfully loaded.'.format(self.base_dir, repo))
                self.print_repository(r)
                # create list of commits then print some of them to stdout
                commits = list(r.iter_commits('master'))[:COMMITS_TO_PRINT]
                for commit in commits:
                    self.print_commit(commit)
                    pass
            else:
                print('Could not load repository at {} :('.format(self.base_dir))

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
                return False, False
            else:
                git_run = subprocess.Popen(git_cmd, cwd=repo_path, stdout=PIPE, stderr=PIPE, shell=True)
                stdout, stderr = git_run.communicate()
                return stdout, stderr
        except Exception as e:
            self.logger.error('Could not run git command: {}. Error is: {}'.format(git_cmd, e))

    def checkout_gitbranch(self, repo_name=None, branch_name=None, new_branch=False, repo_path=None):
        if new_branch is False:
            opts = ''
        else:
            opts = '-b'

        try:
            git_cmd = ['git', 'checkout', opts, branch_name]
            stdout_cb, stderr_cb = self.git_command_run(git_cmd=git_cmd)

            if stdout_cb is not False and stderr_cb is not False:
                if str(stderr_cb).find("fatal: A branch named " + "'" + branch_name + "'" + " already exists.") < 0:
                    self.logger.debug('Could not checkout "{}" branch, there is already a branch of the same name'.
                                      format(branch_name))
                else:
                    self.logger.debug('Checked out "{}" branch successfully.'.format(branch_name))
        except Exception as e:
            self.logger.error("Something went wrong at branch create/checkout! Error: {}". format(e))
            sys.exit(1)
        finally:
            self.logger.debug("Putting you back home - " + self.base_dir)
            os.chdir(self.base_dir)

    @staticmethod
    def get_current_branch():
        try:
            status = str(git("status"))
        except sh.ErrorReturnCode as e:
            raise RuntimeError(e.stderr.decode())

        match = re.match("On branch (\w+)", status)
        current = match.group(1)

        logging.info("In {curr} branch".format(curr=current))

        if status.endswith("nothing to commit, working directory clean\n"):
            logging.debug("Directory clean in {} branch".format(current))
        else:
            raise MergerError("Directory not clean, must commit:\n"
                              "{status}".format(status=status))
        return current

    def pushout_gitbranch(self, branch_name=None, new_branch=False, repo_name=None):
        if new_branch is False:
            opts = ''
        else:
            opts = '-b'

        try:
            checkout_branch = subprocess.Popen(['git', 'checkout', opts, branch_name],
                                               cwd=repo_name, stdout=PIPE, stderr=PIPE, shell=True)
            stdout_cb, stderr_cb = checkout_branch.communicate()

            if str(stderr_cb).find("fatal: A branch named " + "'" + branch_name + "'" + " already exists.") < 0:
                self.logger.debug('Could not checkout "{}" branch, there is already a branch of the same name'.
                                  format(branch_name))
            else:
                self.logger.debug('Checked out "{}" branch successfully.'.format(branch_name))
        except Exception as e:
            self.logger.error("Something went wrong at branch create/checkout!")
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

    @staticmethod
    def print_repository(repo):
        logging.info('Repo description: {}'.format(repo.description))
        logging.info('Repo active branch is {}'.format(repo.active_branch))
        for remote in repo.remotes:
            logging.info('Remote named "{}" with URL "{}"'.format(remote, remote.url))
        logging.info('Last commit for repo is {}.'.format(str(repo.head.commit.hexsha)))

    @Decorators.skip_dryrun
    def cut_new_branch(self, repo_name=None, new_branch=None, from_branch=None, *args, **kwargs):
        try:
            # logging.debug('New Branch name is: {}'.format(new_branch))
            logging.info('Going to cut a new branch for repo="{}", from_branch="{}", new_branch="{}"'.
                         format(repo_name, from_branch, new_branch))
            print("\n\tDo.........\n\tDo.........\n")
            self.checkout_gitbranch(repo_path=self.base_dir + repo_name)
            time.sleep(0.5)
        except Exception as e:
            raise RuntimeError("Something went wrong with the arguments? Err={}".format(e))
            sys.exit(1)

    def load_repo_data(self):
        conf_file = os.path.dirname(os.path.realpath(__file__)) + '/repo.conf'
        self.logger.debug("Reading repo config file from: " + conf_file)
        config = ConfigParser()
        config.read(conf_file)
        logging.debug('Sections found in this config parser are: ' + str(config.sections()))

        return config


class VeraNewBranch(VeraBranchCut):

    def __init__(self, repo_name, repo_url, checkout_branch, new_branchname, *args, **kwargs):
        self.repo_name = repo_name
        self.repo_url = repo_url
        self.checkout_branch = checkout_branch
        self.new_branchname = new_branchname
        self.args = args
        self.kwargs = kwargs


if __name__ == "__main__":

    if sys.version_info[0] < 3:
        print("This script is compatible with python-3.x only")

    logfile = 'vera-branchcut' + time.strftime('%Y_%m_%d_%H_%M' + '.log')
    options = args_extractor()
    logger = setup_logging(opts=options)

    COMMITS_TO_PRINT = 2
    vbc = VeraBranchCut(opts=options, log=logger)
    vbc.main()

    sys.exit(0)
