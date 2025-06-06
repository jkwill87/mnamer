"""Custom exception type definitions."""


class MnamerException(Exception):
    """Base exception for the mnamer package."""


class MnamerSkipException(MnamerException):
    """Raised when the user has chosen to skip renaming the current target."""


class MnamerAbortException(MnamerException):
    """Raised when the user has chosen to quit the application."""


class MnamerNetworkException(MnamerException):
    """Raised when a network request is unaccepted; ie. no internet connection."""


class MnamerNotFoundException(MnamerException):
    """Raised when a lookup or search works as expected yet yields no results."""


class MnamerFailedLangGuesserInstantiation(MnamerException):
    """
    Raised when a requested text language guesser failed to instantiate.
    """


class MnamerNoSuchLangGuesser(MnamerException):
    """Raised when a requested text language guesser name does not match any known guessers."""
