import io
import logging
import os
import platform
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


from app.console_hider import hide_console
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


class UVDownloader:
    def __init__(self, platform_, machine_, app_dir: Path) -> None:
        super().__init__()
        self.platform = platform_
        self.app_dir = app_dir
        self.venv = self.app_dir / ".venv"
        self.machine = machine_
        self.uv_version = "0.10.4"
        self.uv_min_size = 5 * 1024 * 1024
        self.uv_download_timeout = 30  # seconds
        self.uv_download_retries = 3
        self.uv_download_retry_delay = 5  # seconds between retries

    @property
    def arch(self) -> str:
        return "aarch64" if self.machine == "aarch64" else "x86_64"

    @property
    def uv_url(self) -> str:
        if self.platform == "Windows":
            return f"https://github.com/astral-sh/uv/releases/download/{self.uv_version}/uv-x86_64-pc-windows-msvc.zip"
        elif self.platform == "Linux":
            return f"https://github.com/astral-sh/uv/releases/download/{self.uv_version}/uv-{self.arch}-unknown-linux-gnu.tar.gz"
        else:
            raise RuntimeError(f"Unsupported platform: {self.platform}")

    @property
    def uv_path(self) -> Path:
        if self.platform == "Windows":
            return self.app_dir / "uv.exe"
        else:
            return self.app_dir / "uv"

    def download_uv(self) -> None:
        for attempt in range(1, self.uv_download_retries + 1):
            try:
                log.info(
                    f"Downloading uv {self.uv_version} (attempt {attempt}/{self.uv_download_retries})..."
                )
                log.debug(f"URL: {self.uv_url}")

                with urllib.request.urlopen(
                    self.uv_url, timeout=self.uv_download_timeout
                ) as response:
                    zip_data = io.BytesIO(response.read())

                log.debug(
                    f"Archive downloaded, size: {len(zip_data.getvalue()) / 1024 / 1024:.1f} MB"
                )

                if self.platform == "Windows":
                    with zipfile.ZipFile(zip_data) as zf:
                        log.debug(f"Archive contents: {zf.namelist()}")
                        with zf.open("uv.exe") as src, open(self.uv_path, "wb") as dst:
                            dst.write(src.read())

                else:
                    with tarfile.open(fileobj=zip_data, mode="r:gz") as tf:
                        log.debug(f"Archive contents: {tf.getnames()}")
                        member = tf.extractfile(f"uv-{self.arch}-unknown-linux-gnu/uv")
                        if member is None:
                            raise RuntimeError("uv binary not found in archive")
                        with open(self.uv_path, "wb") as dst:
                            dst.write(member.read())
                    self.uv_path.chmod(0o755)

                size = self.uv_path.stat().st_size
                log.debug(
                    f"{self.uv_path.name} written to: {self.uv_path.absolute()} ({size / 1024 / 1024:.1f} MB)"
                )

                if size < self.uv_min_size:
                    self.uv_path.unlink()
                    raise RuntimeError(
                        f"{self.uv_path.name} is suspiciously small ({size} bytes), download may be corrupt. File removed."
                    )

                log.info("uv.exe downloaded successfully")
                return

            except Exception as e:
                log.warning(f"Attempt {attempt} failed: {e}")
                if self.uv_path.exists():
                    self.uv_path.unlink()
                    log.debug(f"Removed incomplete {self.uv_path.name}")
                if attempt < self.uv_download_retries:
                    log.info(f"Retrying in {self.uv_download_retry_delay} seconds...")
                    time.sleep(self.uv_download_retry_delay)

        raise RuntimeError(
            f"Failed to download uv after {self.uv_download_retries} attempts."
        )


def bootstrap(
    app_dir: Path, uv_downloader: UVDownloader, venv: Path, signals: LauncherSignals
) -> None:
    if not uv_downloader.uv_path.exists():
        signals.status_changed.emit(_("Downloading uv..."))
        log.info("uv not found, downloading...")
        uv_downloader.download_uv()

    if not venv.exists():
        signals.status_changed.emit(_("Setting up environment..."))
        log.info("First launch: setting up environment, please wait...")
        subprocess.run(
            [
                uv_downloader.uv_path,
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
    machine_ = platform.machine().lower()
    python = python_path(platform_, venv)
    uv_downloader = UVDownloader(
        platform_=platform_, machine_=machine_, app_dir=app_dir
    )

    signals = LauncherSignals()
    signals.status_changed.connect(lambda text: update_splash(splash, text))
    signals.done.connect(splash.close)
    signals.done.connect(app.quit)

    success = threading.Event()

    def run():
        try:
            bootstrap(
                app_dir=app_dir, uv_downloader=uv_downloader, venv=venv, signals=signals
            )
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
    os.execv(str(python), [str(python), str(app_dir / "main.py")] + sys.argv[1:])


if __name__ == "__main__":
    main()
