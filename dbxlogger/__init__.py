from .args import add_arguments_to
from .logger import Logger
from .exp import Exp, exp_from_args
from .repo import RefFile, get_repo

def StdoutLogger():
    """Create a logger that logs on stdout for quick testing."""
    from .logger import FileLogWriter
    import sys
    return Logger(writer=FileLogWriter(sys.stdout))
