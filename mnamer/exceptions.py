"""mnamer's custom exception type definitions."""


class MnamerException(Exception):
    """Base exception for the mnamer package
    """


class MnamerSkipException(MnamerException):
    """Raised when a user has chosen to skip renaming the current target
    """


class MnamerAbortException(MnamerException):
    """Raised when the user has chosen to quit the application
    """


class MnamerSettingsException(MnamerException):
    """Raised when an error has occurred either loading or saving a config file
    """


class MnamerNetworkException(MnamerException):
    """Raised when a network request is unaccepted; ie. no internet connection.
    """


class MnamerNotFoundException(MnamerException):
    """Raised when a lookup or search works as expected yet yields no results.
    """


class MnamerProviderException(MnamerException):
    """Raised when an endpoint has been used improperly, i.e. invalid API key,
    missing or conflicting parameters.
    """
