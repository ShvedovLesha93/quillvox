import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QSplashScreen

from app.translator import _

WIDTH, HEIGHT = 320, 160


def _build_pixmap(status_text: str) -> QPixmap:
    pixmap = QPixmap(WIDTH, HEIGHT)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background
    painter.setBrush(QColor("#ffffff"))
    painter.setPen(QColor("#e0e0e0"))
    painter.drawRoundedRect(0, 0, WIDTH, HEIGHT, 12, 12)

    # App name
    painter.setFont(QFont("Georgia", 26, QFont.Weight.Bold))
    painter.setPen(QColor("#1a1a1a"))
    painter.drawText(0, 0, WIDTH, 100, Qt.AlignmentFlag.AlignCenter, "QuillVox")

    # Status text
    painter.setFont(QFont("Georgia", 10, QFont.Weight.Normal))
    painter.setPen(QColor("#999999"))
    painter.drawText(0, 90, WIDTH, 40, Qt.AlignmentFlag.AlignCenter, status_text)

    painter.end()
    return pixmap


def _make_flags() -> Qt.WindowType:
    flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
    if sys.platform.startswith("linux"):
        flags |= Qt.WindowType.X11BypassWindowManagerHint
    return flags


def create_splash() -> QSplashScreen:
    splash = QSplashScreen(_build_pixmap(_("Starting...")), _make_flags())
    return splash


def update_splash(splash: QSplashScreen, text: str) -> None:
    """Redraw the splash with updated status text."""
    splash.setPixmap(_build_pixmap(text))
