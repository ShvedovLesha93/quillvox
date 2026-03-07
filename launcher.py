import logging
import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


from app.console_hider import hide_console
from app.constants import BuildConfig
from app.utils.logging_config import configure_logging
from app.views.splash_screen import create_splash, update_splash
from app.translator import _

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    hide_console()

# parse --debug-logging before full logging setup
_debug = "--debug-logging" in sys.argv

configure_logging(console_level=logging.DEBUG if _debug else logging.INFO)
log = logging.getLogger("launcher")


class LauncherSignals(QObject):
    status_changed = Signal(str)
    done = Signal()


def bootstrap(app_dir: Path, uv: Path, venv: Path, signals: LauncherSignals) -> None:
    if not uv.exists():
        msg = (
            f"uv {BuildConfig.UV_VERSION.value} not found at {uv}. "
            "Try reinstalling the application."
        )
        log.error(msg)
        raise RuntimeError(msg)

    if not venv.exists():
        signals.status_changed.emit(_("Setting up environment..."))
        log.info("First launch: setting up environment, please wait...")
        subprocess.run(
            [
                uv,
                "sync",
                "--link-mode",
                "copy",
                "--no-dev",
                "--python-preference",
                "only-managed",
                "--python",
                "3.12",
            ],
            cwd=app_dir,
            check=True,
        )
        log.info("Environment ready.")
    else:
        log.debug("Virtual environment already exists, skipping bootstrap.")


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    else:
        return Path(__file__).resolve().parent


def get_uv_path(app_dir: Path, platform_: str) -> Path:
    if platform_ == "Windows":
        return app_dir / "uv.exe"
    else:
        return app_dir / "uv"


def python_path(platform_: str, venv: Path) -> Path:
    if platform_ == "Windows":
        return venv / "Scripts" / "python.exe"
    else:
        return venv / "bin" / "python"


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    splash = create_splash()
    splash.show()
    app.processEvents()

    app_dir = get_app_dir()
    venv = app_dir / ".venv"
    platform_ = platform.system()
    uv = get_uv_path(app_dir, platform_)
    python = python_path(platform_, venv)

    signals = LauncherSignals()
    signals.status_changed.connect(lambda text: update_splash(splash, text))
    signals.done.connect(splash.close)
    signals.done.connect(app.quit)

    success = threading.Event()

    def run():
        try:
            bootstrap(app_dir=app_dir, uv=uv, venv=venv, signals=signals)
            signals.status_changed.emit(_("Starting..."))
            success.set()
        except Exception as e:
            log.exception(f"Launcher error: {e}")
            signals.status_changed.emit(f"Error: {e}")
            time.sleep(5)
        finally:
            signals.done.emit()

    threading.Thread(target=run, daemon=True).start()
    app.exec()

    if not success.is_set():
        sys.exit(1)

    log.info(f"Launching: {python} {app_dir / 'main.py'}")
    if platform_ == "Windows":
        proc = subprocess.Popen(
            [str(python), str(app_dir / "main.py")] + sys.argv[1:],
            cwd=str(app_dir),
        )
        proc.wait()
        sys.exit(proc.returncode)
    else:
        os.execv(str(python), [str(python), str(app_dir / "main.py")] + sys.argv[1:])


if __name__ == "__main__":
    main()
