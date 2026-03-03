from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QSplashScreen
from app.translator import _


def create_splash() -> QSplashScreen:
    """Create and return a simple splash screen."""
    width, height = 320, 160

    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background
    painter.setBrush(QColor("#ffffff"))
    painter.setPen(QColor("#e0e0e0"))
    painter.drawRoundedRect(0, 0, width, height, 12, 12)

    # App name
    font = QFont("Georgia", 26, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#1a1a1a"))
    painter.drawText(0, 0, width, 100, Qt.AlignmentFlag.AlignCenter, "QuillVox")

    # Subtitle
    font.setPointSize(10)
    font.setWeight(QFont.Weight.Normal)
    painter.setFont(font)
    painter.setPen(QColor("#999999"))
    painter.drawText(0, 90, width, 40, Qt.AlignmentFlag.AlignCenter, _("Starting..."))

    painter.end()

    # Use X11BypassWindowManagerHint on Linux for reliable display
    flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
    import sys

    if sys.platform.startswith("linux"):
        flags |= Qt.WindowType.X11BypassWindowManagerHint

    splash = QSplashScreen(pixmap, flags)
    return splash
