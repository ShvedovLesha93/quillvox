from dataclasses import dataclass
from datetime import datetime
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

    message = Signal(object, str, object)

    def __init__(self) -> None:
        super().__init__()

    def info(self, message: str) -> None:
        self.message.emit(MessageLevel.INFO, message, self.current_time())

    def warning(self, message: str) -> None:
        self.message.emit(MessageLevel.WARNING, message, self.current_time())

    def error(self, message: str) -> None:
        self.message.emit(MessageLevel.ERROR, message, self.current_time())

    def current_time(self) -> str:
        now = datetime.now()
        return now.strftime("%H:%M:%S")


user_msg = UserMessage()
