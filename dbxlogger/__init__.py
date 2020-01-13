"""
:py:mod:`dbxlogger` is a set of Python utility classes and functions that aid
in creating experiments and logs for the **dbx** project.

The two classes that provide the most functionality are the
:py:class:`dbxlogger.Exp` and :py:class:`dbxlogger.Logger` which provide methods
for creating experiments and saving log entries, respectively.

Some of the loggers (like :py:func:`dbxlogger.StdoutLogger` and
:py:class:`dbxlogger.logger.FileLogWriter`) are designed to work without any
:py:class:`dbxlogger.Exp` instance and this can be useful if you are moving to
dbx from an existing project or just trying out the functionality.
"""

import datetime

from .args import add_arguments_to
from .logger import Logger
from .exp import Exp, exp_from_args
from .repo import RefFile, get_repo

def StdoutLogger():
    """Create a logger that logs on stdout for quick testing."""
    from .logger import FileLogWriter
    import sys
    return Logger(writer=FileLogWriter(sys.stdout))

def now():
    """Return current timestamp as :py:class:`datetime.datetime` with UTC timezone."""
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
