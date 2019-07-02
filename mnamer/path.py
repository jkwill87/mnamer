from os.path import join, realpath, split, splitext

__all__ = ["Path"]


class Path:
    """ Simple data class used to represent the segments of a file path
    """

    def __init__(self, path: str):
        directory, relpath = split(realpath(path))
        filename, extension = splitext(relpath)
        self.directory: str = directory
        self.filename: str = filename
        self.extension: str = extension

    @property
    def full(self) -> str:
        return join(self.directory, self.filename) + self.extension

    def __repr__(self) -> str:
        return f'Path("{self.full}")'
