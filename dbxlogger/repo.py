import os
import shutil
from .encoder import DBXEncoder
from .logger import Logger, FileLogWriter
import hashlib


# from https://stackoverflow.com/a/44873382/555516
def sha256sum(filename):
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


class _ExpFile:
    def __init__(self, exp, name, mode="w"):
        self.exp = exp
        self.name = name
        self.mode = mode
        self._sha256 = None

    def _set_sha256(self, digest: str):
        self._sha256 = digest

    def open(self):
        pass

    def close(self):
        pass

    def _done(self):
        """call this method after close() from subclasses."""
        self.exp.add_file(self.name, self.sha256)

    @property
    def sha256(self):
        return self._sha256

    def __dbx_encode__(self):
        return {
            "_dbx": "expfile",
            "exp": self.exp.id,
            "name": self.name,
            "sha256": self._sha256,
        }


class LocalExpFile(_ExpFile):
    """
    Intended usage:

        with exp.file(name, mode) as f:
            # f is a file opened with python's open(name, mode)

    Alternative usage:

        expfile = exp.file(name, mode)
        f = expfile.open()
        # ... f is a file opened with python's open(name, mode) ...
        expfile.close()
    """
    def __init__(self, exp, name, full_path, mode="w"):
        super().__init__(exp, name, mode)
        self.full_path = full_path

    def __enter__(self):
        return self.open()

    def __exit__(self, *args):
        self.close()

    def open(self):
        self._fd = open(self.full_path, self.mode)
        return self._fd

    def close(self):
        self._fd.close()
        self._set_sha256(sha256sum(self.full_path))
        self._done()


class LocalRepo:
    """
    This repo only handles saving experiments and logs locally, it doesn't
    handle querying the repo. All the querying capabilities will be implemented
    separately.
    """

    def __init__(self, path: str):
        self._path = path

    @property
    def path(self):
        return self._path

    def save(self, exp):
        """Save the experiment."""

        output_path = self._pathfor(exp)

        if os.path.exists(output_path):
            # this should almost never happen
            raise Exception("experiment %s (%s) already exists at %s" % (exp.id, exp.name, str(self)))

        os.makedirs(output_path)

        try:
            # write meta
            with open(os.path.join(output_path, "meta.json"), "w") as f:
                json.dump(exp.meta, f, indent=4, sort_keys=True, cls=DBXEncoder)

        finally:
            # cleanup in case of errors
            shutil.rmtree(output_path, ignore_errors=True)

    def _pathfor(self, exp):
        if exp.name:
            return os.path.join(self.path, exp.name, exp.id)

        return os.path.join(self.path, exp.id)

    def logger(self, exp, name=None):
        """Get a new logger for exp with given name or default."""

        if name is None:
            name = "log.jsonl"
        else:
            if not name.endswith("log.jsonl"):
                name += ".log.jsonl"
            if "/" in name or "\\" in name:
                raise Exception("invalid log name %s: log name cannot contain slashes", name)

        if name not in self._loggers:
            self._loggers[name] = self._make_logger(name)

        logpath = os.path.join(self._pathfor(exp), name)
        return Logger(writer=FileLogWriter(logpath, mode="a"))

    def expfile(self, exp, name):
        return LocalExpFile(exp, name, full_path=os.path.join(self._pathfor(exp), name))


    def __str__(self):
        return 'LocalRepo("%s")' % self._path


class RemoteRepo:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("RemoteRepo not yet supported")
