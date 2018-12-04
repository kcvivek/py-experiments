import subprocess


git_cmd = ['git', 'clone', 'git@bitbucket.org:orgdocs/rpm-orgbase.git']

run = subprocess.Popen(git_cmd)

run.communicate()
