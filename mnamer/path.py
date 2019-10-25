from os import path

__all__ = ["Path"]


class Path:
    """Simple data class used to represent the segments of a file path.
    """

    def __init__(self, directory: str, filename: str, extension: str):
        self.directory = path.realpath(directory)
        self.filename = filename
        self.extension = extension.lstrip(".")

    @classmethod
    def parse(cls, file_path: str):
        file_path = path.expanduser(file_path)
        directory, file = path.split(file_path)
        filename, extension = path.splitext(file)
        return cls(directory, filename, extension)

    @property
    def full(self) -> str:
        return f"{path.join(self.directory, self.filename)}.{self.extension}"

    def __repr__(self) -> str:
        return f'Path("{self.directory}","{self.filename}","{self.extension}")'

    def __str__(self):
        return self.full
