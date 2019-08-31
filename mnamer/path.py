from os.path import expanduser, join, realpath, split, splitext

__all__ = ["Path"]


class Path:
    """Simple data class used to represent the segments of a file path.
    """

    def __init__(self, directory: str, filename: str, extension: str):
        self.directory = realpath(directory)
        self.filename = filename
        self.extension = extension.lstrip(".")

    @classmethod
    def parse(cls, path: str):
        path = expanduser(path)
        directory, file = split(path)
        filename, extension = splitext(file)
        return cls(directory, filename, extension)

    @property
    def full(self) -> str:
        return f"{join(self.directory, self.filename)}.{self.extension}"

    def __repr__(self) -> str:
        return f'Path("{self.directory}","{self.filename}","{self.extension}")'

    def __str__(self):
        return self.full
