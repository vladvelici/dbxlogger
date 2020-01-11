import datetime
import socket
import json
import os
import sys

import nanoid

from . import libgit
from .encoder import DBXEncoder
from .repo import get_repo

RESERVED_KEYS = set([
    "createdAt",
    "kind",
    "cmd",
    "params",
    "name",
    "git",
    "env",
    "_dbx",
])


_ID_ALPHABET = '_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def _generate_random_id():
    return nanoid.generate(size=13, alphabet=_ID_ALPHABET)

class CustomMetaKeyNotSupportedError(Exception):
    def __init__(self, k):
        super().__init__("Custom meta key not supported: %s" % k)

def params_from_args(args):
    return {k: v for k,v in vars(args).items()}

def exp_from_args(args, kind=None, args_to_ignore=None, params=None, extra_meta=None, env=True, git=True):
    """Shortcut to use savedir and name from command line args.

    Params
        args: args as returned by argparse
        kind: experiment kind (string), if not given it uses the name of the script,
        args_to_ignore: array of arg names not to add as experiment params,
        params: params to add to the args (overrides ones parsed from args if already exist)
        extra_meta: extra metadata for the experiment
    """

    repo = get_repo(args)

    params_ = params_from_args(args)
    if args_to_ignore is not None:
        for k in args_to_ignore:
            del params_[k]

    # remove default args that should not be params (repo and exp name)
    for k in ["name", "repo"]:
        if k in params_:
            del params_[k]

    if params is not None:
        params_.update(params)

    name = args.name

    if kind is None:
        kind = os.path.basename(sys.argv[0])

    return Exp(
        repo=repo,
        kind=kind,
        params=params_,
        name=name,
        extra_meta=extra_meta,
        env=env,
        git=git)


class Exp:

    def __init__(self, repo, kind, params=None, name=None, extra_meta=None, env=True, git=True):
        self._id = _generate_random_id()
        self._repo = repo
        self._kind = kind
        self._name = name

        if params is not None:
            self._params = params
        else:
            self._params = {}

        self.extra_meta = extra_meta
        self._save_env = env
        self._save_git = git

        # empty loggers dict
        self._loggers = {}

        # execution environment
        self._cmd = None
        self._pwd = None
        self._script = None
        self._hostname = None

        self._created_at = None
        self._meta = None

        self._files = {}
        self._saved = False # whether this experiment was saved in the repo

    @property
    def id(self):
        return self._id

    @property
    def files(self):
        return self._files

    def cmd():
        doc = "command to run for this experiment."
        def fget(self):
            if self._cmd is None:
                self._cmd = sys.argv
            return self._cmd
        def fset(self, value):
            self._cmd = value
        def fdel(self):
            self._cmd = None
        return locals()
    cmd = property(**cmd())

    def pwd():
        doc = "command to run for this experiment."
        def fget(self):
            if self._pwd is None:
                self._pwd = os.getcwd()
            return self._pwd
        def fset(self, value):
            self._pwd = value
        def fdel(self):
            self._pwd = None
        return locals()
    pwd = property(**pwd())

    def script():
        doc = "script that ran this experiment"
        def fget(self):
            if self._script is None:
                self._script = os.path.abspath(sys.argv[0])
            return self._script
        def fset(self, value):
            self._script = value
        def fdel(self):
            del self._script
        return locals()
    script = property(**script())

    def hostname():
        doc = "hostname for the running machine"
        def fget(self):
            if self._hostname is None:
                self._hostname = socket.gethostname()
            return self._hostname
        def fset(self, value):
            self._hostname = value
        def fdel(self):
            del self._hostname
        return locals()
    hostname = property(**hostname())

    def created_at():
        doc = "date experiment was created - always use UTC timestamps!"
        def fget(self):
            if self._created_at is None:
                self._created_at = datetime.datetime.utcnow()
            return self._created_at
        def fset(self, value):
            self._created_at = value
        def fdel(self):
            self._created_at = None
        return locals()
    created_at = property(**created_at())

    @property
    def kind(self):
        return self._kind

    @property
    def name(self):
        return self._name

    @property
    def repo(self):
        return self._repo

    @property
    def meta(self):
        """Return the meta content (for meta.json). Does not compute it if not
        already generated."""
        return self._meta

    @property
    def params(self):
        # no need to guard it with a copy, since exp.params[k] = v should be
        # permitted
        return self._params

    def __getitem__(self, k):
        """Get experiment param shortcut."""
        return self._params[k]

    def __setitem__(self, k, v):
        """Set experiment param shortcut."""
        self._params[k] = v

    def _compute_meta(self):
        meta = {
            "id": self._id,
            "createdAt": self.created_at,
            "kind": self.kind,
            "params": self._params,
            "name": self.name,
            "cmd": self.cmd,
            "pwd": self.pwd,
            "hostname": self.hostname,
            "script": self.script,
        }

        meta = self._add_extra_meta(meta)

        if self._save_env:
            meta["env"] = _get_env()

        if self._save_git:
            git_info = _get_git()
            if not git_info:
                # print something out on stderr instead of failing the run
                print("WARN: no git repo found, omitting meta['git']", file=sys.stderr)
            else:
                meta["git"] = git_info

        self._meta = meta
        return meta

        meta_path = os.path.join(self.path, "meta.json")

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=4, sort_keys=True, cls=DBXEncoder)

    def _add_extra_meta(self, meta):
        """Mutates the meta dict and returns it."""

        if self.extra_meta is None:
            return meta
        for k, v in self.extra_meta:
            if k in RESERVED_KEYS:
                raise CustomMetaKeyNotSupportedError(k)
            meta[k] = v
        return meta

    def save(self):
        if self._saved:
            raise Exception("cannot save experiment twice")

        self._compute_meta()
        self._repo.save(self)

        self._saved = True

    def logger(self, name=None):
        if not self._saved:
            raise Exception("cannot get logger for unsaved experiment")

        if name is None:
            name = "log.jsonl"
        else:
            if not name.endswith("log.jsonl"):
                name += ".log.jsonl"
            if "/" in name or "\\" in name:
                raise Exception("invalid log name %s: log name cannot contain slashes", name)

        if name not in self._loggers:
            logger = self._repo.logger(self, name)
            self._loggers[name] = logger
            return logger

        return self._loggers[name].root()

    def file(self, name, mode="w"):
        if not self._saved:
            raise Exception("cannot attempt to create a file in unsaved experiment")

        return self._repo.expfile(self, name, mode=mode)

    def filepath(self, name : str):
        """Create an exp file by name. For local repos it simply gives you the
        correct path to save an exp file at. For remote repos if there's no
        local repo used as well, it creates a temp file and returns it.

        After the path has been used, the file is saved as an expfile with the
        give name.

        Use the `.file()` method as much as possible. This is intended to add
        compatibility with libraries that only take a path as parameter but not
        a file descriptor.

        Example:

            with exp.filepath("checkpoint3.tar.pth") as path:
                model.save(path)

        """
        raise NotImplementedError()

    def _add_file(self, name, hash):
        """This method is called after a new file has been added to the
        experiment."""

        self._files[name] = hash
        self._repo.save_fileindex(self)


def _get_git():
    branch, commit, commit_long, is_git_repo = libgit.current()
    if not is_git_repo:
        return None
    else:
        uncommited_changes = libgit.has_changes()
        return {
            "branch": branch,
            "commit": commit,
            "commit_long": commit_long,
            "uncommited_changes": uncommited_changes,
        }


def _get_env():
    return {k: v for k, v in os.environ.items()}
