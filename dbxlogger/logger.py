import json
import os
import multiprocessing
import threading
from contextlib import contextmanager

from .encoder import DBXEncoder
from .stopwatch import stopwatch

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
        return self

    def parent(self):
        if len(self._path) > 0:
            self._path = self._path[:-1]
        return self

    def root(self):
        self._path.clear()
        return self

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


class Event:
    def __init__(self, full_name, data=None, save_duration=True):
        self.full_name = full_name
        if data is None:
            data = {}
        self._data = data
        self._save_duration = save_duration
        if self._save_duration:
            self._stopwatch = stopwatch()
        self._computed = False

    def delete(self, key):
        if key in self._data:
            del self._data[key]

    def add(self, data, v=None):
        """Add data to event. Can be used to change data too. To delete keys
        from the event, use `.del(key)`.

        Usage:
            .add(key, value)        # add one key-value pair
            .add({ ... })           # add all from given dict
        """
        if v is not None:
            # expecting .add(key, value) call
            if "duration" == data and self._save_duration:
                raise Exception("cannot add 'duration' event data and have save_duration True")
            self._data[data] = v
        else:
            # expecting .add(dict) call
            if "duration" in data and self._save_duration:
                raise Exception("cannot add 'duration' event data and have save_duration True")
            self._data.update(data)
        return self

    def _get_data(self):
        # don't change data if its already computed to keep timing ok
        if self._computed:
            return self._data

        self._computed = True
        if self._save_duration:
            self._data["duration"] = self._stopwatch()

        return self._data


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

        for epoch in range(10):
            with self.log.at("training/epoch/%d" % epoch):
                self.train_one_epoch()

    Or even simpler

        for epoch in self.log.iter_at(range(10), lambda epoch: "training/epoch/%d" % epoch):
            # now self.log.ctx == "training/epoch/<epoch>"
            self.train_one_epoch()

        # self.log.ctx is resumed to root (or whatever it was before the loop)

    This class is defined in :py:class:`dbxlogger.logger.Logger` but is availabe
    at :py:class:`dbxlogger.Logger` as a shortcut.
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

    def new_subprocess(file_path, mode="w", context=None):
        """Same as new() but creates a logger that launches the LogWriter on a
        different process to minimize I/O blocking. See SubprocessLogWriter for
        details."""

        w = SubprocessLogWriter(file_path, mode)
        if context is None:
            context = LogContext()
        return Logger(writer=w, context=context)

    def new_thread(file_path, mode="w", context=None):
        """Same as new() but creates a logger that launches the LogWriter on a
        different thread to minimize I/O blocking. See ThreadLogWriter for
        details."""

        w = ThreadLogWriter(file_path, mode)
        if context is None:
            context = LogContext()
        return Logger(writer=w, context=context)

    def __init__(self, writer=None, context=None):
        self._writer = writer
        if context is None:
            self._context = LogContext()
        else:
            self._context = context

    def new_event(self, name, **kwargs):
        full_name = self.local_event_name(name)
        return Event(full_name, **kwargs)

    @property
    def ctx(self):
        return self._context

    @property
    def writer(self):
        return self._writer

    def __call__(self, event, data=None):
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

    def local_event_name(self, event):
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
        return "/".join(full_event)

    def log(self, event, data=None):
        if isinstance(event, Event):
            if data is not None:
                event.add(data)
            data = event._get_data()
            self.writer.log(event.full_name, data)
        else:
            if data is None:
                raise Exception("cannot use None data for inline events")
            event = self.local_event_name(event)
            self.writer.log(event, data)

    def close(self):
        self.writer.close()

    @contextmanager
    def at(self, path):
        current_path = [p for p in self.ctx.path]

        if path.startswith("/"):
            path = path[1:]
            self.ctx.path = path
        else:
            self.ctx.sub(path)

        try:
            yield
        finally:
            self.ctx.path = current_path

    def at_iter(self, iterator, path_lambda_or_fmt):
        current_path = [p for p in self.ctx.path]
        for obj in iterator:
            self.ctx.path = current_path

            if type(path_lambda_or_fmt) == str:
                path = path_lambda_or_fmt % obj
            else:
                path = path_lambda_or_fmt(obj)


            if path.startswith("/"):
                self.ctx.path = path[1:]
            else:
                self.ctx.sub(path)

            yield obj

        self.ctx.path = current_path


class FileLogWriter:
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

        self._encoder = DBXEncoder

    def log(self, event_name, data):
        if "event" in data:
            del data["event"]
        encoded = json.dumps(data, sort_keys=True, cls=self._encoder)
        event_encoded = json.dumps({"event": event_name})
        print(event_encoded[:-1], ", ", encoded[1:], file=self.f, sep="")
        self.f.flush()

    def close(self):
        self.f.flush()
        self.f.close()


class SubprocessLogWriter:
    def __init__(self, file_path, mode="w", writer_class=None):
        """file_path and mode are passed to LogWriter() in another process."""
        self.file_path = file_path
        self.mode = mode

        if writer_class is None:
            self.writer_class = FileLogWriter
        else:
            self.writer_class = writer_class

        self.queue = multiprocessing.Queue(10)
        self.proc = multiprocessing.Process(
            target=SubprocessLogWriter.writer_main,
            args=(self.writer_class, self.file_path, self.mode, self.queue)
        )
        self.proc.start()

    def writer_main(writer_class, file_path, mode, queue):
        w = writer_class(file_path, mode)
        for message in queue:
            if message is None:
                w.flush()
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

class ThreadLogWriter:
    def __init__(self, file_path, mode="w", writer_class=None, queue_size=10):
        """file_path and mode are passed to LogWriter() in another process."""
        self.file_path = file_path
        self.mode = mode

        if writer_class is None:
            self.writer_class = FileLogWriter
        else:
            self.writer_class = writer_class

        self.queue = threading.Queue(queue_size)
        self.thread = threading.Thread(
            target=ThreadLogWriter.writer_main,
            args=(self.writer_class, self.file_path, self.mode, self.queue)
        )
        self.thread.start()

    def writer_main(writer_class, file_path, mode, queue):
        w = writer_class(file_path, mode)
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
