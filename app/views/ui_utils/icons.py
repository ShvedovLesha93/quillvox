from enum import Enum
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QPushButton,
)

import app.resources.resources_rc

FLAT_ICON_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.15);
}

QPushButton:disabled {
    background-color: transparent;
}
"""


class IconName(str, Enum):
    PAUSE = "pause"
    PLAY_ARROW = "play_arrow"
    REPLAY = "replay"
    SPEED = "speed"
    STOP = "stop"
    VOLUME_OFF = "volume_off"
    VOLUME_UP = "volume_up"


def get_icon(name: str) -> QIcon:
    """Get icon from resources"""
    return QIcon(f":/icons/icons/{name}.svg")


class IconButton(QPushButton):
    BASE_ICON_SIZE = 28
    BASE_BUTTON_PADDING = 4

    def __init__(self, name: IconName, scale: float = 1.0, parent=None) -> None:
        super().__init__(parent)
        self.name = name
        self.scale = scale

        self.setIcon(get_icon(self.name.value))
        self.setStyleSheet(FLAT_ICON_BUTTON_STYLE)
        self.setFlat(True)

        # Setup opacity effect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._update_opacity()

        self.set_scale(self.scale)

    def set_scale(self, scale: float) -> None:
        """Set the button scale factor."""
        self.scale = scale
        icon_size = int(self.BASE_ICON_SIZE * scale)
        button_size = icon_size + (self.BASE_BUTTON_PADDING * 2)

        self.setIconSize(QSize(icon_size, icon_size))
        self.setFixedSize(button_size, button_size)

    def set_icon(self, name: IconName) -> None:
        self.name = name
        self.setIcon(get_icon(name.value))

    def _update_opacity(self) -> None:
        """Update opacity based on enabled state."""
        self._opacity_effect.setOpacity(1.0 if self.isEnabled() else 0.3)

    def changeEvent(self, event: QEvent) -> None:
        """Automatically update opacity when enabled state changes."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange:
            self._update_opacity()


class IconLabel(QLabel):
    BASE_ICON_SIZE = 28
    BASE_PADDING = 4

    def __init__(
        self,
        name: IconName,
        scale: float = 1.0,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.name = name
        self.scale = scale

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.set_icon(name)
        self.set_scale(scale)

    def set_scale(self, scale: float) -> None:
        self.scale = scale

        icon = int(self.BASE_ICON_SIZE * scale)
        size = icon + self.BASE_PADDING * 2

        self.setFixedSize(size, size)
        self._update_pixmap(icon)

    def set_icon(self, name: IconName) -> None:
        self.name = name
        self._update_pixmap()

    def _update_pixmap(self, icon_size: int | None = None) -> None:
        icon_size = icon_size or int(self.BASE_ICON_SIZE * self.scale)

        pixmap = get_icon(self.name.value).pixmap(
            icon_size,
            icon_size,
        )
        self.setPixmap(pixmap)
