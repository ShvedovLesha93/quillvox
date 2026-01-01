import sys
from PySide6.QtWidgets import QApplication
from app.models.main_model import MainModel
from app.view_model.main_vm import MainViewModel
from app.views.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")

    main_model = MainModel()
    main_vm = MainViewModel(main_model)

    view = MainWindow(main_vm)
    view.move(1020, 320)

    view.show()
    sys.exit(app.exec())
