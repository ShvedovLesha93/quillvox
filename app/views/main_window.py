from pathlib import Path
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.view_model.file_selector import FileSelectorVM
from app.views.menu_bar import MenuBar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.f_select_vm = FileSelectorVM()

        self.menu_bar = MenuBar(self)
        self._setup_ui()
        self._setup_status_bar()

    def _setup_status_bar(self):
        status_bar = self.statusBar()
        self.status_message = QLabel("Ready")
        status_bar.addWidget(self.status_message)

    def _setup_ui(self) -> None:
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

    def open_file(self):
        filter = self.f_select_vm.filter
        last_filter = self.f_select_vm.last_filter
        last_dir = self.f_select_vm.last_dir

        file, last_filter = self._open_file_dialog(
            filter=filter, last_filter=last_filter, last_dir=str(last_dir)
        )
        if file and last_filter:
            self.f_select_vm.on_file_selected(file)
            self.f_select_vm.last_filter = last_filter

    def _open_file_dialog(
        self, filter: str, last_filter: str, last_dir: str
    ) -> tuple[Path, str]:
        file_dialog = QFileDialog()
        file, filter = file_dialog.getOpenFileName(
            self,
            caption="Open media file",
            filter=filter,
            selectedFilter=last_filter,
            dir=last_dir,
        )

        return Path(file), filter
