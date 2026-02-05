import logging
import multiprocessing
import sys
from PySide6.QtWidgets import QApplication
from app.config.general_config import GeneralConfig
from app.models.main_model import MainModel
from app.utils.logging_config import configure_logging
from app.theme_manager import ThemeManager
from app.view_model.main_vm import MainViewModel
from app.views.main_window import MainWindow

from app.translator import language_manager


import atexit


def main():
    multiprocessing.freeze_support()

    result = configure_logging(console_level=logging.DEBUG)
    if result:
        log_queue, log_listener = result
        # Ensure listener stops even on unexpected exit
        atexit.register(log_listener.stop)
    else:
        log_queue = None
        log_listener = None

    app = QApplication([])
    app.setStyle("Fusion")

    general_config = GeneralConfig()
    language_manager.set_language(general_config.language)

    main_model = MainModel()
    theme_manager = ThemeManager(app, initial_theme=general_config.theme)

    main_vm = MainViewModel(
        app=app,
        general_config=general_config,
        main_model=main_model,
        theme_manager=theme_manager,
        log_queue=log_queue,
    )

    view = MainWindow(app=app, theme_manager=theme_manager, main_vm=main_vm)
    view.move(1020, 320)
    view.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
