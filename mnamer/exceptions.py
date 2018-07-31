class MnamerException(Exception):
    """ Base exception for the mnamer package
    """


class MnamerConfigException(MnamerException):
    """ Raised when an error has occurred either loading or saving a config file
    """


class MnamerQuitException(MnamerException):
    """ Raised when a user requests to quit the program
    """


class MnamerSkipException(MnamerException):
    """ Raised when a user skips an entry
    """
