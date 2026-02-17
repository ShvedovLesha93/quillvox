import argparse
import shutil
from pathlib import Path
import subprocess

from app.constants import FrozenPath

from app.utils.logging_config import configure_logging

import logging

logger = logging.getLogger(__name__)

DIST_PATH = Path("dist/QuillVox")


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


def copy_files(copy_from: Path, to_folder: str, include: str) -> None:
    for f in copy_from.rglob(include):
        relative = f.relative_to(copy_from)
        target = DIST_PATH / to_folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)


def copy_manager() -> None:
    import app.resources.styles as styles
    import app.locales as locales

    styles_path = Path(styles.__file__).parent
    locales_path = Path(locales.__file__).parent

    copy_files(styles_path, to_folder=FrozenPath.STYLES.value, include="*.qss")
    logger.info("*.qss files copied")
    copy_files(locales_path, to_folder=FrozenPath.LOCALES.value, include="*.mo")
    logger.info("locales copied")


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
        copy_manager()
    else:
        logger.critical("Build failed: %s,", err)


if __name__ == "__main__":
    main()
