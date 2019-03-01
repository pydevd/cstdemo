class _Exception(Exception):
    """Base class for project exceptions classes."""

    def __init__(self, msg: str):
        self.msg = msg


class FileUploadError(_Exception):
    """Exception class for any errors related to file upload process"""


class FlacConversionError(_Exception):
    """Exception class for any errors related to conversion process"""
