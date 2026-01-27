from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QPalette, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.views.ui_utils.icons import IconButton, IconName

from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.theme_manager import ThemeManager
    from app.views.main_window import MainWindow


class NotificationsView(QWidget):
    def __init__(
        self,
        main_window: MainWindow | None = None,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.theme_manager = theme_manager

        self.wrap_enabled = False

        self.messages: list[tuple[str, QPalette.ColorRole | str]] = []

        self._setup_ui()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.update_theme)

    def _setup_ui(self) -> None:
        self.resize(500, 400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text)

        self.btn_toggle_wrap = IconButton(IconName.FORMAT_TEXT_WRAP)
        self.btn_toggle_wrap.clicked.connect(self.toggle_wrap)
        layout.addWidget(self.btn_toggle_wrap, alignment=Qt.AlignmentFlag.AlignCenter)

    def update_theme(self, theme_mode: ThemeMode) -> None:
        self._rerender_messages()

    def _rerender_messages(self) -> None:
        self.text.clear()
        for text, color in self.messages:
            self._append_text(text, color)

    def append_message(self, text: str, color: QPalette.ColorRole | str) -> None:
        self.messages.append((text, color))
        self._append_text(text, color)

    def _append_text(self, text: str, color: QPalette.ColorRole | str) -> None:
        if isinstance(color, QPalette.ColorRole):
            palette = QApplication.palette()
            qcolor = palette.color(QPalette.ColorGroup.Active, color)
        else:
            qcolor = QColor(color)

        cursor = self.text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(qcolor))

        cursor.setCharFormat(fmt)
        cursor.insertText(text + "\n")

        self.text.setTextCursor(cursor)

    def set_wrap_state(self, state: bool) -> None:
        if state:
            # Enable wrapping
            self.set_btn_tooltip()
            self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            self.btn_toggle_wrap.set_icon(IconName.FORMAT_TEXT_OVERFLOW)
        else:
            # Disable wrapping
            self.set_btn_tooltip()
            self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            self.btn_toggle_wrap.set_icon(IconName.FORMAT_TEXT_WRAP)

    def retranslate(self) -> None:
        self.set_btn_tooltip()

    def set_btn_tooltip(self) -> None:
        if self.wrap_enabled:
            self.btn_toggle_wrap.setToolTip(_("Disable text wrapping"))
        else:
            self.btn_toggle_wrap.setToolTip(_("Enable text wrapping"))

    @Slot()
    def toggle_wrap(self):
        print("Toggled")
        print(f"before self.wrap_enabled: {self.wrap_enabled}")
        self.wrap_enabled = not self.wrap_enabled
        print(f"after self.wrap_enabled: {self.wrap_enabled}")
        self.set_wrap_state(self.wrap_enabled)

    def showEvent(self, event):
        super().showEvent(event)
        if self.main_window is not None:
            main_center = self.main_window.frameGeometry().center()
            geom = self.frameGeometry()
            geom.moveCenter(main_center)
            self.move(geom.topLeft())


# ============ TEST ============
if __name__ == "__main__":
    text = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla eros tortor, sollicitudin ac ipsum quis, aliquam sollicitudin erat. Integer ullamcorper, purus vel mattis lobortis, sapien metus congue ligula, id blandit magna eros id nibh. Maecenas sagittis aliquet nulla. Curabitur id neque in nulla hendrerit venenatis quis vel ex. Donec convallis nulla dolor, at suscipit ligula mollis sit amet. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. In mollis diam dui, eget posuere nisl vestibulum ut. Donec eu nunc dictum, volutpat augue eu, fringilla lectus. Donec accumsan elit vel faucibus imperdiet. Nulla imperdiet magna ut rhoncus pellentesque. Pellentesque odio erat, vestibulum a tortor fringilla, hendrerit feugiat velit. Aliquam vestibulum est sit amet est fringilla euismod. Quisque pellentesque id dolor eget convallis.

Ut odio sapien, sagittis non lobortis eu, lobortis sed tortor. Sed rutrum elementum turpis. Nulla convallis laoreet ipsum, nec mattis enim ornare ut. Vestibulum nec leo sed ex egestas laoreet. Sed et nunc at arcu porta viverra. Nullam dictum porttitor congue. Vestibulum non pretium magna.

Pellentesque a lectus id lacus tempus bibendum eu quis nisl. Vestibulum eleifend purus magna, et commodo velit maximus quis. In lorem felis, tincidunt laoreet odio congue, malesuada posuere enim. Duis vitae metus cursus, molestie dolor sed, pulvinar sem. Vestibulum tellus magna, ultricies vitae augue et, ullamcorper pretium turpis. Maecenas lobortis nunc vitae tellus tincidunt, eu cursus erat facilisis. Vivamus a pulvinar mi, ut finibus tellus. Pellentesque euismod et mauris eget malesuada. Curabitur semper, lacus sed commodo pulvinar, risus tellus luctus lectus, nec condimentum risus massa non enim.

Nam urna eros, gravida et metus non, lacinia volutpat diam. Quisque auctor sodales hendrerit. Vestibulum maximus enim in ullamcorper egestas. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Nullam at quam volutpat, luctus nulla a, vestibulum lorem. Nunc mattis egestas justo, id pretium ex viverra in. Nulla scelerisque felis in tellus tempor pulvinar. Maecenas accumsan cursus feugiat.

Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Nam quam felis, rhoncus nec finibus id, vehicula varius orci. Nullam rhoncus metus ac ligula varius, faucibus vulputate nibh eleifend. Vestibulum sapien nunc, euismod in lectus vel, vulputate scelerisque felis. Sed egestas mollis felis ac mattis. Pellentesque laoreet et orci non congue. Vestibulum ipsum turpis, faucibus vitae nibh eget, scelerisque pharetra justo. Vestibulum convallis a massa eget euismod. Nulla varius nibh nisi, ac pulvinar quam blandit finibus. Sed vitae felis sit amet lorem accumsan tincidunt non id odio. In pharetra diam ut lacus sollicitudin pulvinar. Morbi varius blandit arcu id sodales.
    """
    from PySide6.QtWidgets import QApplication
    from app.theme_manager import ThemeManager
    from app.constants import ThemeMode

    app = QApplication([])
    app.setStyle("Fusion")

    theme_manager = ThemeManager(app, ThemeMode.LIGHT)

    view = NotificationsView()
    view.text.setPlainText(text)
    view.move(1020, 320)

    view.show()
    app.exec()
