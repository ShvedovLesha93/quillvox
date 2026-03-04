import platform
import sys
import tarfile
from app.console_hider import hide_console, show_console
import time
import io
import logging
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from rich.logging import RichHandler

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    hide_console()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("launcher")

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

VENV = APP_DIR / ".venv"

_system = platform.system()
_machine = platform.machine().lower()

if _system == "Windows":
    UV = APP_DIR / "uv.exe"
    PYTHON = VENV / "Scripts" / "python.exe"
else:
    UV = APP_DIR / "uv"
    PYTHON = VENV / "bin" / "python"

UV_VERSION = "0.10.4"
UV_MIN_SIZE = 5 * 1024 * 1024  # 5 MB — uv.exe is ~10 MB

if _system == "Windows":
    UV_URL = f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-pc-windows-msvc.zip"
elif _system == "Linux":
    _arch = "aarch64" if _machine == "aarch64" else "x86_64"
    UV_URL = f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-{_arch}-unknown-linux-gnu.tar.gz"
else:
    raise RuntimeError(f"Unsupported platform: {_system}")

UV_DOWNLOAD_TIMEOUT = 30  # seconds
UV_DOWNLOAD_RETRIES = 3
UV_DOWNLOAD_RETRY_DELAY = 5  # seconds between retries


def log_paths():
    log.debug(f"APP_DIR : {APP_DIR}")
    log.debug(f"UV      : {UV} (exists: {UV.exists()})")
    log.debug(f"VENV    : {VENV} (exists: {VENV.exists()})")
    log.debug(f"PYTHON  : {PYTHON} (exists: {PYTHON.exists()})")


def download_uv() -> None:
    for attempt in range(1, UV_DOWNLOAD_RETRIES + 1):
        try:
            log.info(
                f"Downloading uv {UV_VERSION} (attempt {attempt}/{UV_DOWNLOAD_RETRIES})..."
            )
            log.debug(f"URL: {UV_URL}")

            with urllib.request.urlopen(
                UV_URL, timeout=UV_DOWNLOAD_TIMEOUT
            ) as response:
                zip_data = io.BytesIO(response.read())

            log.debug(
                f"Archive downloaded, size: {len(zip_data.getvalue()) / 1024 / 1024:.1f} MB"
            )

            if _system == "Windows":
                with zipfile.ZipFile(zip_data) as zf:
                    log.debug(f"Archive contents: {zf.namelist()}")
                    with zf.open("uv.exe") as src, open(UV, "wb") as dst:
                        dst.write(src.read())

            else:
                with tarfile.open(fileobj=zip_data, mode="r:gz") as tf:
                    log.debug(f"Archive contents: {tf.getnames()}")
                    member = tf.extractfile(f"uv-{_arch}-unknown-linux-gnu/uv")
                    if member is None:
                        raise RuntimeError("uv binary not found in archive")
                    with open(UV, "wb") as dst:
                        dst.write(member.read())
                UV.chmod(0o755)

            size = UV.stat().st_size
            log.debug(
                f"{UV.name} written to: {UV.absolute()} ({size / 1024 / 1024:.1f} MB)"
            )

            if size < UV_MIN_SIZE:
                UV.unlink()
                raise RuntimeError(
                    f"{UV.name} is suspiciously small ({size} bytes), download may be corrupt. File removed."
                )

            log.info("uv.exe downloaded successfully")
            return

        except Exception as e:
            log.warning(f"Attempt {attempt} failed: {e}")
            if UV.exists():
                UV.unlink()
                log.debug(f"Removed incomplete {UV.name}")
            if attempt < UV_DOWNLOAD_RETRIES:
                log.info(f"Retrying in {UV_DOWNLOAD_RETRY_DELAY} seconds...")
                time.sleep(UV_DOWNLOAD_RETRY_DELAY)

    raise RuntimeError(f"Failed to download uv after {UV_DOWNLOAD_RETRIES} attempts.")


def bootstrap() -> bool:
    """Returns True if bootstrap was needed (console should stay visible briefly)."""
    needs_bootstrap = not UV.exists() or not VENV.exists()

    if needs_bootstrap and IS_FROZEN:
        show_console()

    if not UV.exists():
        log.info("uv not found, downloading...")
        download_uv()

    if not VENV.exists():
        log.info("First launch: setting up environment, please wait...")
        subprocess.run(
            [
                UV,
                "sync",
                "--link-mode",
                "copy",
                "--no-dev",
                "--python-preference",
                "only-managed",
                "--python",
                "3.12",
            ],
            cwd=APP_DIR,
            check=True,
        )
        log.info("Environment ready.")
        log.debug(f"PYTHON  : {PYTHON} (exists: {PYTHON.exists()})")
    else:
        log.debug("Virtual environment already exists, skipping bootstrap.")

    return needs_bootstrap


def main():
    try:
        log_paths()
        did_bootstrap = bootstrap()

        if did_bootstrap and IS_FROZEN:
            hide_console()

        log.info(f"Launching: {PYTHON} {APP_DIR / 'main.py'}")
        result = subprocess.run([PYTHON, APP_DIR / "main.py"])

        if result.returncode != 0:
            if IS_FROZEN:
                show_console()
            log.error(f"App exited with error code: {result.returncode}")
            input("\nPress Enter to close...")
            sys.exit(result.returncode)

    except Exception as e:
        if IS_FROZEN:
            show_console()
        log.exception(f"Launcher error: {e}")
        input("\nPress Enter to close...")
        sys.exit(1)


if __name__ == "__main__":
    main()
