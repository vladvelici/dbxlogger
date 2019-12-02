
class File:
    """
    File is the base class for logging a file using MLV Logger.

    This logs not only the file path but also a checksum of the file to be able
    to check for integrity when loading it back from disk, which is done
    automatically when using any of the MLV reading libraries.

    The file is encoded in the log as its path, hash and last modified time.

    The path can be to any of the supported storage systems. Currently local
    filesystem only with support to handle files that belong to MLV experiments.
    """

    def __init__(self, path):
        self.path = path


class ExpFile(File):
    """
    ExpFile is a MLV File that is stored in the same folder as the experiment
    itself.

    This class isn't used for actually writing files to disk, but to aid doing
    so. The main use is to log ExpFiles by referencing them correctly in the log
    and metadata.
    """

    def from_path(relpath):
        """Create an ExpFile from relpath, the file is already stored on disk."""
        pass

    def from_bytes(relpath, bytes):
        pass
