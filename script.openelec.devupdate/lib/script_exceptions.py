class Canceled(Exception):
    pass

class WriteError(IOError):
    pass

class DecompressError(IOError):
    pass