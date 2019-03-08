import json
import os
import multiprocessing

class LogContext:
    """Helper class to keep track of Logger context without polluting the Logger
    class too much. Not indented for use outisde of the Logger class."""

    def __init__(self, path=None):
        self._path = []
        if path is not None:
            self.sub(path)

    def sub(self, path):
        if type(path) is str:
            if "/" in path:
                self._path.extend(path.split("/"))
            else:
                self._path.append(path)
        else: # assume some iterable
            self._path.extend(path)

    def parent(self):
        if len(self._path) > 0:
            self._path = self._path[:-1]

    def root(self):
        self._path.clear()

    def copy(self):
        return LogContext(self._path)

    def path():
        doc = "Get and set the path of this context."
        def fget(self):
            return self._path
        def fset(self, value):
            self.root()
            self.sub(value)
        return locals()
    path = property(**path())


class Logger:
    """
    The general purpose Logger object. Create one with `new()` or
    `new_subprocess()` and start logging events from your programs.

    A logger has a `context` which helps you write less lengthy event names. You
    can also make (cheap) copies of your main Logger object so you don't modify
    your main logger context. Related methods are: sub() and parent().

    Note that navigation from child to parent does NOT create a graph of Logger
    objects. The navigation is simply done by context path. This might be a
    little confusing in the following example:

        log = Logger(...)
        a = log.sub("hello/world/example/1")

        a.ctx.path
        # -> ["hello", "world", "example", "1"]

        a.parent().ctx.path
        # -> ["hello", "world", "example"]

    Or you can choose to modify the context of your main logger using the
    `.context` property, for example:

        self.log = Logger(...)
        for epoch in range(10):
            self.log.ctx.sub("training/epoch/%d" % epoch)
            self.train_one_epoch()
        self.log.context.root()

    This second option is useful if you don't want to pass Logger objects to
    methods. The first option is useful if you want to always keep your root
    logger intact and if you typically pass logger objects as arguments.
    """

    def new(file_path, mode="w", context=None):
        """Create a new logger at the given file path.

        mode: is the file opening mode.
        context: a LogContext object or None to create a new one automatically.
        """

        if context is None:
            context = LogContext()
        w = LogWriter(file_path, mode)
        return Logger(writer=w, context=context)

    def new_subprocess(file_path, mode="w"):
        """Same as new() but creates a logger that launches the LogWriter on
        a different process to minimize I/O blocking. See SubprocessLogWriter
        for details."""

        w = SubprocessLogWriter(file_path, mode)
        if context is None:
            context = LogContext()
        return Logger(writer=w, context=context)

    def __init__(self, writer=None, context=None):
        self._writer = writer
        self._context = context

    @property
    def ctx(self):
        return self._context

    @property
    def writer(self):
        return self._writer

    def __call__(self, event, data):
        """Handy shortcut for calling .log(event, data)."""
        self.log(event, data)

    def sub(self, path):
        """Copy this logger and set the context to path (relative to current
        context)."""

        ctx = self.ctx.copy()
        ctx.sub(path)
        return Logger(writer=self._writer, context=ctx)

    def parent(self):
        """Copy this logger and set the context to one level higher than the
        current context path."""
        ctx = self.ctx.copy()
        ctx.parent()
        return Logger(writer=self._writer, context=ctx)

    def root(self):
        """Copy this logger and set the context to the root level."""
        ctx = self.ctx.copy()
        ctx.root()
        return Logger(writer=self._writer, context=ctx)

    def log(self, event, data):
        full_event = []
        full_event.extend(self.ctx.path)
        if type(event) == str:
            if "/" in event:
                full_event.extend(event.split("/"))
            else:
                full_event.append(event)
        else:
            # assume array of strings
            full_event.extend(event)
        event = "/".join(full_event)
        self.writer.log(event, data)

    def close(self):
        self.writer.close()


class LogWriter:
    def __init__(self, file_path, mode="w"):
        """Create a LogWriter.

        file_path: path to a file as string or a file object
        mode: if file_path is a string, the mode used to open the file
        """
        if type(file_path) == str:
            self.file_path = file_path
            self.f = open(file_path, mode)
        else:
            self.f = file_path

    def log(self, event, data):
        self._log(event, data)

    def _log(self, full_event, data):
        data["event"] = full_event
        json.dump(f, data, indent=0, sort_keys=True)
        self.f.flush()

    def close(self):
        self.f.flush()
        self.f.close()


class SubprocessLogWriter:
    def __init__(self, file_path, mode="w"):
        """file_path and mode are passed to LogWriter() in another process."""
        self.file_path = file_path
        self.mode = mode
        self.queue = multiprocessing.Queue(10)
        self.proc = multiprocessing.Process(
            target=SubprocessLogWriter.writer_main,
            args=(self.file_path, self.mode, self.queue)
        )
        self.proc.start()

    def writer_main(file_path, mode, queue):
        w = LogWriter(file_path, mode)
        for message in queue:
            if message is None:
                w.close()
                return
            event, data = message
            w.log(event, data)

        # shouldn't get here, but if it does, close the file
        w.close()

    def log(self, event, data):
        self.queue.put((event, data))

    def close(self):
        self.queue.put(None)
        self.proc.join()
