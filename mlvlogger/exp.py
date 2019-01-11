import sys
import os
import json

RESERVED_KEYS = set([
    "createdAt",
    "kind",
    "cmd",
    "params",
    "name",
    "git",
    "env",
    "_mlv",
])

def params_from_args(args):
    return args.to_dict()

def add_git_params(args):
    pass

def params_from_environment(args):
    pass

class CustomMetaKeyNotSupportedError(Exception):
    def __init__(self, k):
        super().__init__("Custom meta key not supported: %s" % k)

class Exp:
    """
    Exp class is how you create an experiment that automatically saves all the
    metadata required, creates all the folder necessary and writes the metadata
    parameters into a `meta.json` file.

    The output path of the experiment is a folder resolved by two parameters:
    the experiment name and the name of the experiment. The output path is
    simply `os.path.join(savedir, name)`.

    If the experiment output path already exists, a new path is created by
    appending "_N" where N is an auto-increment number starting at 1 to the
    experiment name.

    Parameters:

        savedir:        the directory where experiments are saved
        name:           the name of this experiment
        kind:           the kind (or type) of this experiment
        extra_meta:     any extra key-values to save to meta.json root
                        (not under "params:")
        environment:    whether to save all the environment variables into "env"
                        key in meta.json
        git:            whether to save git information if available: branch,
                        commit, current diff if not everything is commited,
                        remote URL(s) and local repo path
    """

    def __init__(self, savedir, name, params, kind, extra_meta=None, environment=True, git=True):
        self._savedir = savedir
        self._name = name
        self._params = params
        self._kind = kind

        self.extra_meta = extra_meta
        self.environment = environment
        self.git = git

        # path not computed yet
        self._o = None

    def _compute_path(self):
        """Append necessary numbers at the end of the experiment name if
        necessary."""
        path = os.path.join(self.savedir, self.name)
        num = 1
        while not os.path.exists(path):
            path = os.path.join(self.savedir, self.name+"_"+num)
            num += 1
        return path

    @property
    def kind(self):
        return self._kind

    @property
    def path(self):
        """The output folder of the experiment."""
        if self._o is None:
            self._o = self._compute_path()
        return self._o

    @property
    def abspath(self):
        """The absolute output path of the experiment."""
        return os.path.abspath(self.path)

    @property
    def name(self):
        return self._name

    @property
    def savedir(self):
        return self._savedir

    def write(self):
        self.create_dirs()
        self.write_meta()

    def write_meta(self):
        # create and write a metafile based on params
        meta = {
            "createdAt": datetime.datetime.utcnow(),
            "kind": self.kind,
            "cmd": sys.argv,
            "params": self.params,
            "name": self.name,
        }

        meta = self._add_extra_meta(meta)

    def _add_extram_meta(self, meta):
        """Mutates the meta, returns it for clarity when it's used."""

        if self.extra_meta is not None:
            return meta
        for k, v in self.extra_meta:
            if k in RESERVED_KEYS:
                raise CustomMetaKeyNotSupportedError(k)
            meta[k] = v
        return meta

    def create_dirs(self):
        os.makedirs(self.path)

    def get_git(self):
        pass

    def get_env(self):
        pass
