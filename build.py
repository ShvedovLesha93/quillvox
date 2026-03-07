import argparse
import io
import platform
import shutil
from pathlib import Path
import subprocess
import tarfile
import time
import urllib.request
import zipfile

from app.constants import BuildConfig
from app.utils.logging_config import configure_logging

import logging

log = logging.getLogger(__name__)

APP_PATH = Path("app")
DIST_PATH = Path("dist")
INCLUDE = ["main.py", "uv.lock", "pyproject.toml", "version.json"]


class UVDownloader:
    def __init__(self, dist: Path) -> None:
        super().__init__()
        self.platform = platform.system()
        self.machine = platform.machine().lower()
        self.dist = dist
        self.venv = self.dist / ".venv"
        self.uv_version = BuildConfig.UV_VERSION.value
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
    def uv_cache_path(self) -> Path:
        if self.platform == "Windows":
            return Path(".cache") / "uv" / self.uv_version / "uv.exe"
        else:
            return Path(".cache") / "uv" / self.uv_version / "uv"

    @property
    def uv_path(self) -> Path:
        if self.platform == "Windows":
            return self.dist / "uv.exe"
        else:
            return self.dist / "uv"

    def download_uv(self) -> None:
        # Use cached binary if available
        if self.uv_cache_path.exists():
            log.info("uv %s found in cache, copying...", self.uv_version)
            self.uv_cache_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.uv_cache_path, self.uv_path)
            log.info("uv copied from cache to %s", self.uv_path)
            return

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

                log.info("%s downloaded successfully", self.uv_path.name)

                # Save to cache for future builds
                self.uv_cache_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.uv_path, self.uv_cache_path)
                log.info("uv cached at %s", self.uv_cache_path)
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


def run_pyinstaller() -> tuple[bool, str | None]:
    cmd = ["uv", "run", "pyinstaller", "main.spec"]
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        for line in process.stdout:  # pyright: ignore
            line = line.rstrip()
            if line:
                log.debug("[pyinstaller] %s", line)

        process.wait()
        if process.returncode != 0:
            return (False, f"PyInstaller exited with code {process.returncode}")

        return (True, None)
    except Exception as e:
        return (False, str(e))


def collect_files() -> None:
    shutil.copytree(
        APP_PATH,
        DIST_PATH / "app",
        ignore=shutil.ignore_patterns("__pycache__", "*.po", "*.pot", "*.pyc"),
    )

    for file in INCLUDE:
        shutil.copy(file, DIST_PATH / file)


def remove_collected_files() -> None:
    collected_dirs = [DIST_PATH / "app"]
    collected_files = [DIST_PATH / file for file in INCLUDE]

    for dir_path in collected_dirs:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            log.info("Removed: %s", dir_path)

    for file_path in collected_files:
        if file_path.exists():
            file_path.unlink()
            log.info("Removed: %s", file_path)


def clean() -> bool:
    """Clean previous builds."""

    dirs_to_clean = ["dist"]
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                log.info("Removed: %s", dir_name)
            except PermissionError:
                log.error("Folder removal is prohibited: %s", dir_path)
                return False
    return True


def main() -> None:
    uv_downloader = UVDownloader(dist=DIST_PATH)

    parser = argparse.ArgumentParser(description="Build Python app using PyInstaller")
    parser.add_argument(
        "--clean", action="store_true", help="Clean dist before building"
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="Disable file logging, output to console only",
    )
    args = parser.parse_args()

    configure_logging(
        console_level=logging.DEBUG,
        file_level=logging.DEBUG,
        file_log_name=Path(__file__).stem,
        show_module_name=False,
        file_logging=not args.no_log_file,
    )

    if args.clean:
        if not clean():
            return
    else:
        remove_collected_files()

    result, err = run_pyinstaller()
    if result:
        log.info("PyInstaller build complete")
        collect_files()
        if not uv_downloader.uv_path.exists():
            uv_downloader.download_uv()
    else:
        log.critical("Build failed: %s,", err)


if __name__ == "__main__":
    main()
