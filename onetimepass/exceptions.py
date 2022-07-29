class BaseApplicationException(Exception):
    pass


class UnhandledFormatException(BaseApplicationException):
    def __init__(self, format_):
        super().__init__(format_)


class UnhandledOTPTypeException(BaseApplicationException):
    def __init__(self, otp_type):
        super().__init__(otp_type)
