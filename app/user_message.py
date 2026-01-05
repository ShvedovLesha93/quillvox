from enum import Enum
from PySide6.QtCore import QObject, Signal


class MessageLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class UserMessage(QObject):
    """
    Logger for user-facing messages.
    Emits signals based on message level.
    """

    message = Signal(MessageLevel, str)

    def __init__(self) -> None:
        super().__init__()

    def info(self, message: str) -> None:
        self.message.emit(MessageLevel.INFO, message)

    def warning(self, message: str) -> None:
        self.message.emit(MessageLevel.WARNING, message)

    def error(self, message: str) -> None:
        self.message.emit(MessageLevel.ERROR, message)


user_msg = UserMessage()
