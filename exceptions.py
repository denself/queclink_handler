
class ProtocolException(Exception):
    pass


class BadProtocolFormat(ProtocolException):
    pass


class MessageNotImplemented(ProtocolException):
    pass


class MessageFormatException(ProtocolException):
    pass


class StreamClosedError(Exception):
    pass


class SessionRequiredError(Exception):
    pass
