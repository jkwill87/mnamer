""" mnamer's custom exception type definitions
"""


class MnamerException(Exception):
    """ Base exception for the mnamer package
    """


class MnamerSkipException(MnamerException):
    """ Raised when a user has chosen to skip renaming the current target
    """


class MnamerAbortException(MnamerException):
    """ Raised when the user has chosen to quit the application
    """


class MnamerConfigException(MnamerException):
    """ Raised when an error has occurred either loading or saving a config file
    """
