class BaseApplicationException(Exception):
    pass


class UnhandledFormatException(BaseApplicationException):
    def __init__(self, format_):
        super().__init__(format_)
