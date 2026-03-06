from __future__ import annotations
import os
from typing import TYPE_CHECKING
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)
import logging
from pathlib import Path
import platform
import tarfile
import urllib.request

if TYPE_CHECKING:
    from app.view_model.main_vm import MainViewModel


APP_DIR = Path(__file__).parent.parent
APP_NAME = "QuillVox"
LOG_FILE = APP_DIR / "app.updater.log"

log = logging.getLogger("updater")

log.debug(f"__file__: {Path(__file__).resolve()}")
log.debug(f"APP_DIR resolved to: {APP_DIR.resolve()}")


def download_release(version: str, main_vm: MainViewModel) -> None:
    system = platform.system()
    if system == "Linux":
        filename = f"{APP_NAME}.tar.gz"
    elif system == "Windows":
        filename = f"{APP_NAME}.zip"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    url = f"https://github.com/ShvedovLesha93/quillvox/releases/download/v{version}/{filename}"
    archive_path = APP_DIR / filename

    log.info(f"Downloading {version} from: {url}")
    log.debug(f"Archive will be saved to: {archive_path.resolve()}")

    try:
        with Progress(
            "[progress.description]{task.description}",
            BarColumn(bar_width=40, complete_style="green", finished_style="green"),
            "[progress.percentage]{task.percentage:>3.0f}%",
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task(f"Downloading {filename}", total=None)

            def on_progress(block_count, block_size, total_size):
                downloaded = min(block_count * block_size, total_size)
                if progress.tasks[task].total is None and total_size > 0:
                    progress.update(task, total=total_size)
                progress.update(task, completed=downloaded)

            urllib.request.urlretrieve(url, archive_path, reporthook=on_progress)

        log.info(f"Saved to: {archive_path.resolve()}")
        _extract_and_replace(archive_path)
    finally:
        if archive_path.exists():
            archive_path.unlink()
            log.debug(f"Cleaned up archive: {archive_path}")

    log.info("Restarting app...")
    main_vm.restart_application()


def _extract_and_replace(archive_path: Path) -> None:
    log.info(f"Extracting {archive_path.name} into {APP_DIR.resolve()}")

    old_exe = APP_DIR / APP_NAME
    backup_exe = APP_DIR / f"{APP_NAME}.old"

    if old_exe.exists():
        old_exe.rename(backup_exe)
        log.debug(f"Backed up old binary to: {backup_exe}")

    try:
        with tarfile.open(archive_path, "r:gz") as tf:
            members = tf.getmembers()
            log.debug(f"Archive contains {len(members)} entries")
            for member in members:
                tf.extract(member, path=APP_DIR, filter="data")
                log.debug(f"Extracted: {member.name}")

        if old_exe.exists():
            old_exe.chmod(0o755)

        if backup_exe.exists():
            backup_exe.unlink()

        log.info("Extraction complete.")

    except Exception as e:
        log.error(f"Extraction failed: {e}")
        if backup_exe.exists() and not old_exe.exists():
            backup_exe.rename(old_exe)
            log.error("Restored old binary from backup.")
        raise


def restart_app() -> None:
    log.info("Restarting app...")
    os.execv(APP_DIR / APP_NAME, [APP_DIR / APP_NAME])


def run(version: str, main_vm: MainViewModel) -> None:
    download_release(version, main_vm)
