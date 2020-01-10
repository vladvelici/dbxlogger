"""Simple utility to check git exit codes, etc.

Has many limitations but it is good enough for now.
"""

import subprocess

def has_changes():
    """Returns whether the current directory has uncommitted changes to any
    track files."""

    unstaged = subprocess.Popen('git diff --exit-code', shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    unstaged.communicate()
    unstaged_code = unstaged.returncode

    if unstaged_code != 0:
        return True

    uncommitted = subprocess.Popen('git diff --cached --exit-code', shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    uncommitted.communicate()
    uncommitted_code = uncommitted.returncode

    if uncommitted_code != 0:
        return True

    return False

def current():
    """Returns the current branch and the current commit SHA"""

    p = subprocess.Popen("git show", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commit, err = p.communicate()

    is_git_repo = p.returncode == 0
    if not is_git_repo:
        return "", "", "", False

    commit = commit.split()[1]

    p = subprocess.Popen("git symbolic-ref --short HEAD", shell=True, stdout=subprocess.PIPE)
    branch, err = p.communicate()

    p = subprocess.Popen("git log --pretty=fuller -1", shell=True, stdout=subprocess.PIPE)
    commit_long, err = p.communicate()

    return branch.decode(), commit.decode(), commit_long.decode(), is_git_repo
