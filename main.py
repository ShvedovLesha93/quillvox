from __future__ import annotations
import argparse
from pathlib import Path
from app.config.general_config import GeneralConfig
from app.translator import language_manager, _
import logging
import multiprocessing
import sys
import atexit
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication, QSplashScreen
    from multiprocessing import Queue


def main():
    crash_dialog_enabled = True
    parser = argparse.ArgumentParser(description="Audio transcription desktop app")

    parser.add_argument(
        "--debug-logging",
        action="store_true",
        help="Enable debug logging (sets log level to DEBUG)",
    )
    parser.add_argument(
        "--no-crash-dialog",
        action="store_true",
        help="Disable crash dialog on fatal error",
    )
    # fmt: off
    parser.add_argument(
        "--audio",
        type=Path,
        help="Path to the audio file"

    )
    # fmt: on
    args = parser.parse_args()
    audio: Path | None = args.audio
    if audio and not audio.exists():
        raise FileNotFoundError(f"File '{audio}' not found")

    crash_dialog_enabled = not args.no_crash_dialog
    debug_logging_enabled = args.debug_logging

    general_config = GeneralConfig()
    language_manager.set_language(general_config.language)
    splash = None

    try:
        from PySide6.QtWidgets import QApplication
        from app.views.splash_screen import create_splash

        app = QApplication([])
        app.setStyle("Fusion")
        splash = create_splash()
        splash.show()

        _run_app(
            app=app,
            splash=splash,
            general_config=general_config,
            debug=debug_logging_enabled,
            audio=audio,
        )
    except Exception:
        if splash:
            splash.hide()
        if crash_dialog_enabled:
            _show_crash_dialog()
        raise


def init_logging(level: int) -> Queue | None:
    from app.utils.logging_config import configure_logging

    result = configure_logging(
        multiprocessing_mode=True, console_level=level, file_level=level
    )
    if result:
        log_queue, log_listener = result
        atexit.register(log_listener.stop)
        return log_queue
    else:
        log_queue = None
        log_listener = None
        return log_queue


def _run_app(
    app: QApplication,
    splash: QSplashScreen,
    general_config: GeneralConfig,
    debug=False,
    audio: Path | None = None,
) -> None:
    from app.models.main_model import MainModel
    from app.theme_manager import ThemeManager
    from app.view_model.main_vm import MainViewModel
    from app.views.main_window import MainWindow

    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    queue = init_logging(level)
    main_model = MainModel()
    theme_manager = ThemeManager(app, initial_theme=general_config.theme)

    main_vm = MainViewModel(
        app=app,
        general_config=general_config,
        main_model=main_model,
        theme_manager=theme_manager,
        log_queue=queue,
    )

    view = MainWindow(app=app, theme_manager=theme_manager, main_vm=main_vm)
    view.move(1020, 200)
    view.show()

    if audio:
        main_vm.file_selector_vm.open_selected_file(audio)

    splash.finish(view)  # Waits for view to appear before closing splash

    sys.exit(app.exec())


def _show_crash_dialog():
    """Show a crash dialog when the app fails to start."""
    import traceback

    # Get the full traceback as a string
    error_text = traceback.format_exc()

    # Log it to a file first (always, regardless of what happens next)
    log_path = None
    try:
        with open("crash.log", "w", encoding="utf-8") as f:
            f.write(error_text)
            log_path = Path(f.name).absolute()
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
        msg.setWindowTitle(_("QuillVox - Startup Error"))
        msg.setText(_("QuillVox failed to start due to an unexpected error."))
        msg.setInformativeText(
            _("A crash log has been saved to:\n{log_path}").format(log_path=log_path)
        )
        msg.setDetailedText(error_text)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg.exec()

    except Exception:
        # Qt itself failed - last resort: show the console with the error
        try:
            from app.console_hider import show_console

            show_console()
        except Exception:
            pass

        print(_("QuillVox crashed during startup:"), file=sys.__stderr__ or sys.stderr)
        print(error_text, file=sys.__stderr__ or sys.stderr)
        input(_("Press Enter to exit..."))


if __name__ == "__main__":
    multiprocessing.freeze_support()

    if sys.platform == "win32":
        try:
            multiprocessing.set_start_method("spawn", force=True)
        except RuntimeError:
            pass

    main()
