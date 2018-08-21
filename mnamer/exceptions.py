class MnamerException(Exception):
    """ Base exception for the mnamer package
    """


class MnamerConfigException(MnamerException):
    """ Raised when an error has occurred either loading or saving a config file
    """
