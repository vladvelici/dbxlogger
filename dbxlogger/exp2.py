import socket

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

        self._saved = False # whether this experiment was saved in the repo

    def cmd():
        doc = "command to run for this experiment."
        def fget(self):
            if self._cmd is None:
                self._cmd = os.arvg
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
                self._script = os.path.abspath(os.argv[0])
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
        return this._kind

    @property
    def name(self):
        return this._name

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
            "createdAt": self.createdAt,
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
            meta["env"] = self._get_env()

        if self._save_git:
            git_info = self._get_git()
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

    def save(self):
        if self._saved:
            raise Exception("cannot save experiment twice")

        self._compute_meta()
        self._repo.save(exp)

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

        return self._loggers[name]

    def file(self, name):
        if not self._saved:
            raise Exception("cannot attempt to save file in unsaved experiment")

        return self._repo.expfile(exp, name)
