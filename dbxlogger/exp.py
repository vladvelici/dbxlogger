import sys
import os
import json
import datetime

from . import libgit
from .logger import Logger
from .encoder import DBXEncoder

import nanoid

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

def params_from_args(args):
    return {k: v for k,v in vars(args).items()}

class CustomMetaKeyNotSupportedError(Exception):
    def __init__(self, k):
        super().__init__("Custom meta key not supported: %s" % k)

class Exp:
    """
    Exp class represents an experiments and provides an API to perform common
    operations like saving an experiment and creating a logger.

    Exp class works regardless of where the current repo is stored: local or
    remote via the dbx server.

    Exp class is how you create an experiment that automatically saves all the
    metadata required, creates all the folder necessary and writes the metadata
    parameters into a `meta.json` file.

    The output path of the experiment is a folder resolved by two parameters:
    the experiment name and the name of the experiment. The output path is
    simply `os.path.join(repo, name, id)` if that path doesn't already exist.

    Experiment names are not necessarily unique. They only aid organisation of
    experiments within projects.

    Parameters:

        repo:           the directory where experiments are saved
        name:           the name of this experiment
        kind:           the kind (or type) of this experiment
        extra_meta:     any extra key-values to save to meta.json root
                        (not under "params:"). useful for plugins.
        env:            whether to save all the environment variables into "env"
                        key in meta.json
        git:            whether to save git information if available: branch,
                        commit, current diff if not everything is commited,
                        remote URL(s) and local repo path
    """

    def __init__(self, repo, name, params, kind, extra_meta=None, env=True, git=True):
        self._id = _generate_random_id()
        self._repo = repo
        self._name = name
        if self._name is None:
            self._name = self._id
        self._params = params
        self._kind = kind

        self.extra_meta = extra_meta
        self._save_env = env
        self._save_git = git

        # path not computed yet
        self._o = None

        # empty loggers dict
        self._loggers = {}

    def new_from_args(args, kind=None, args_to_ignore=None, params=None, extra_meta=None, env=True, git=True):
        """Shortcut to use savedir and name from command line args.

        Params
            args: args as returned by argparse
            kind: experiment kind (string), if not given it uses the name of the script,
            args_to_ignore: array of arg names not to add as experiment params,
            params: params to add to the args (overrides ones parsed from args if already exist)
            extra_meta: extra metadata for the experiment
        """

        params_ = params_from_args(args)
        if args_to_ignore is not None:
            for k in args_to_ignore:
                del params_[k]

        # remove default args that should not be params (repo and exp name)
        for k in ["name", "repo"]:
            del params_[k]

        if params is not None:
            params_.update(params)

        name = args.name

        if kind is None:
            kind = os.path.basename(sys.argv[0])

        return Exp(args.repo, name, params_, kind, extra_meta, env, git)

    def _compute_path(self):
        """Append necessary numbers at the end of the experiment name if
        necessary."""
        path = os.path.join(self.repo, self.name)
        num = 1
        while os.path.exists(path):
            path = os.path.join(self.repo, self.name+"_"+str(num))
            num += 1
        return path

    @property
    def kind(self):
        return self._kind

    @property
    def maybe_path(self):
        """Resolved output folder of the experiment. If write() or create_dirs()
        wasn't called it returns the most-likely path, but it might not be the
        path the experiment gets saved in.

        Concatenated repo and name (<repo>/<name>[_i]). If folder exists
        an underscore and a number are appended to the folder name to make it
        unique.

        Folder is not created before write() or create_dirs() methods are
        called, and the output path will be recalculated. This makes the path
        property unreliable until after write() or create_dirs() was called.
        """
        if self._o is None:
            return self._compute_path()
        return self._o

    @property
    def path(self):
        """Returns the final path of this experiment. Returns None if called
        before the final path is known (before write() or create_dirs() was
        called)."""
        return self._o

    @property
    def abspath(self):
        """The absolute output path of the experiment."""
        return os.path.abspath(self.path)

    @property
    def name(self):
        return self._name

    @property
    def repo(self):
        return self._repo

    @property
    def params(self):
        # create a copy of params and return it, so users can't change it via
        # directly changing this dict
        return {k: v for k, v in self._params.items}

    def write(self):
        self.create_dirs()
        self.write_meta()

    def write_meta(self):
        # create and write a metafile based on params
        meta = {
            "id": self._id,
            "createdAt": datetime.datetime.utcnow(),
            "kind": self.kind,
            "cmd": sys.argv,
            "params": self._params,
            "name": self.name,
        }

        meta = self._add_extra_meta(meta)

        if self._save_env:
            meta["env"] = self._get_env()

        if self._save_git:
            git_info = self._get_git()
            if not git_info:
                # fail by priting something out on stderr instead of failing the run
                print("WARN: no git repo found, omitting meta['git']", file=sys.stderr)
            else:
                meta["git"] = git_info

        meta_path = os.path.join(self.path, "meta.json")

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=4, sort_keys=True, cls=DBXEncoder)

    def path_for(self, file_name):
        """Helper method to get a usable path to the experiment folder, useful
        for storing ExpFiles."""
        return os.path.join(self.path, file_name)

    def _add_extra_meta(self, meta):
        """Mutates the meta dict and returns it."""

        if self.extra_meta is None:
            return meta
        for k, v in self.extra_meta:
            if k in RESERVED_KEYS:
                raise CustomMetaKeyNotSupportedError(k)
            meta[k] = v
        return meta

    def create_dirs(self):
        self._o = self._compute_path()
        os.makedirs(self._o)

    def _get_git(self):
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

    def _get_env(self):
        return {k: v for k, v in os.environ.items()}

    def _make_logger(self, name):
        """Create a logger by name. name is assumed to already end with
        `log.jsonl`."""

        exppath = self.path
        if exppath is None:
            raise Exception("cannot initiate logger before calling exp.write()")

        return Logger.new(os.path.join(self.path, name))

    def logger(self, name=None):
        """Returns a logger instance for the named Log Stream. If name is None
        (default), the default log stream is used."""

        if name is None or name == "":
            name = "log.jsonl"
        else:
            if not name.endswith("log.jsonl"):
                name += ".log.jsonl"
            if "/" in name or "\\" in name:
                raise Exception("invalid log name %s: log name cannot contain slashes", name)

        if name not in self._loggers:
            self._loggers[name] = self._make_logger(name)

        # always return a root logger
        return self._loggers[name].root()
