import sys
from PySide6.QtWidgets import QApplication
from app.constants import ThemeMode
from app.models.main_model import MainModel
from app.utils.logging_config import configure_logging
from app.view_model.main_vm import MainViewModel
from app.theme_manager import ThemeManager
from app.views.main_window import MainWindow


def main():
    configure_logging()

    app = QApplication([])
    app.setStyle("Fusion")

    main_model = MainModel()
    theme_manager = ThemeManager(app, initial_theme=ThemeMode.SYSTEM)
    main_vm = MainViewModel(app=app, main_model=main_model, theme_manager=theme_manager)
    view = MainWindow(app=app, theme_manager=theme_manager, main_vm=main_vm)
    view.move(1020, 320)

    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
