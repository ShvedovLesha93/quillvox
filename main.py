import sys
from PySide6.QtWidgets import QApplication
from app.views.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    view = MainWindow()

    view.show()
    sys.exit(app.exec())
