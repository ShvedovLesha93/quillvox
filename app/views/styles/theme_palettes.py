from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtGui import QColor, QPalette


if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


def dark_palette(app: QApplication) -> None:
    """Configure dark mode palette for Fusion style.

    Args:
        app: QApplication instance
    """
    dark_palette = QPalette()

    # Base colors
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(50, 50, 50))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(40, 40, 40))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(66, 133, 244))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(66, 133, 244))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    # Disabled colors
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(100, 100, 100)
    )
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(100, 100, 100),
    )
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(100, 100, 100),
    )

    app.blockSignals(True)
    app.setPalette(dark_palette)
    app.blockSignals(False)


def light_palette(app: QApplication) -> None:
    """Configure light mode palette for Fusion style.

    Args:
        app: QApplication instance
    """
    light_palette = QPalette()

    # Base colors
    light_palette.setColor(QPalette.ColorRole.Window, QColor(253, 253, 253))
    light_palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
    light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(30, 30, 30))
    light_palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
    light_palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
    light_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ColorRole.Link, QColor(0, 102, 204))
    light_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    light_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    # Disabled colors
    light_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(160, 160, 160)
    )
    light_palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(160, 160, 160),
    )
    light_palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(160, 160, 160),
    )

    app.setPalette(light_palette)
