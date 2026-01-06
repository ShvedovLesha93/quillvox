from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Title(QWidget):
    def __init__(
        self,
        parent=None,
        text: str = "",
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(text)
        self.title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title.setWordWrap(True)
        self.title.setWordWrap(True)

        layout.addWidget(self.title)

    def setTitle(self, text: str) -> None:
        self.title.setText(text)
