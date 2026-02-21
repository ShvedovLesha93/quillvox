import argparse
import shutil
from pathlib import Path
import subprocess

from app.utils.logging_config import configure_logging

import logging

logger = logging.getLogger(__name__)

APP_PATH = Path("app")
DIST_PATH = Path("dist")


def run_pyinstaller() -> tuple[bool, str | None]:
    cmd = ["uv", "run", "pyinstaller", "main.spec"]
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        for line in process.stdout:  # pyright: ignore
            line = line.rstrip()
            if line:
                logger.debug("[pyinstaller] %s", line)

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

    for file in ["main.py", "uv.lock", "pyproject.toml"]:
        shutil.copy(file, DIST_PATH / file)


def clean() -> bool:
    """Clean previous builds."""

    dirs_to_clean = ["dist"]
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                logger.info("Removed: %s", dir_name)
            except PermissionError:
                logger.error("Folder removal is prohibited: %s", dir_path)
                return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Python app using PyInstaller")

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

    if not clean():
        return

    result, err = run_pyinstaller()
    if result:
        logger.info("PyInstaller build complete")
        collect_files()
    else:
        logger.critical("Build failed: %s,", err)


if __name__ == "__main__":
    main()
