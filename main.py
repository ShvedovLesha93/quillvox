import logging
import multiprocessing
import sys
import atexit


def main():
    if getattr(sys, "frozen", False):
        from app.console_hider import hide_console

        hide_console()

    try:
        _run_app()
    except Exception:
        _show_crash_dialog()
        raise


def _run_app():
    from PySide6.QtWidgets import QApplication
    from app.config.general_config import GeneralConfig
    from app.models.main_model import MainModel
    from app.utils.logging_config import configure_logging
    from app.theme_manager import ThemeManager
    from app.view_model.main_vm import MainViewModel
    from app.views.main_window import MainWindow
    from app.translator import language_manager

    logger = logging.getLogger(__name__)

    result = configure_logging(console_level=logging.DEBUG, file_level=logging.DEBUG)
    if result:
        log_queue, log_listener = result
        atexit.register(log_listener.stop)
    else:
        log_queue = None
        log_listener = None

    if sys.platform == "win32":
        try:
            multiprocessing.set_start_method("spawn", force=True)
        except RuntimeError:
            pass
        logger.debug("set_start_method: spawn")

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
    view.move(1020, 200)
    view.show()

    sys.exit(app.exec())


def _show_crash_dialog():
    """Show a crash dialog when the app fails to start."""
    import traceback

    # Get the full traceback as a string
    error_text = traceback.format_exc()

    # Log it to a file first (always, regardless of what happens next)
    try:
        with open("crash.log", "w", encoding="utf-8") as f:
            f.write(error_text)
    except Exception:
        pass

    # Try to show a GUI crash dialog
    try:
        # Try to show a Qt message box
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import Qt

        # QApplication may or may not exist at this point
        app = QApplication.instance() or QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("QuillVox - Startup Error")
        msg.setText("QuillVox failed to start due to an unexpected error.")
        msg.setInformativeText("A crash log has been saved to:\n" "crash.log")
        msg.setDetailedText(error_text)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg.exec()

    except Exception:
        # Qt itself failed - last resort: show the console with the error
        if getattr(sys, "frozen", False):
            try:
                from app.console_hider import show_console

                show_console()
            except Exception:
                pass

        print("QuillVox crashed during startup:", file=sys.__stderr__ or sys.stderr)
        print(error_text, file=sys.__stderr__ or sys.stderr)
        input("Press Enter to exit...")  # Keep console open so user can read it


if __name__ == "__main__":
    multiprocessing.freeze_support()

    if sys.platform == "win32":
        try:
            multiprocessing.set_start_method("spawn", force=True)
        except RuntimeError:
            pass

    main()
