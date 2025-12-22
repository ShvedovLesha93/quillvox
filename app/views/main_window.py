from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from app.views.menu_bar import MenuBar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.menu_bar = MenuBar(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

    def open_file_dialog(self) -> tuple[str, str]:
        file_dialog = QFileDialog()
        file, filter = file_dialog.getOpenFileName(self, caption="Open media file")

        return file, filter


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    view = MainWindow()

    view.show()
    app.exec()
