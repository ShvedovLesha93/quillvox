import os
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


APP_DIR = Path(__file__).parent

APP_NAME = "QuillVox"
LOG_FILE = APP_DIR / "app.updater.log"

log = logging.getLogger("launcher")


def download_release(version: str) -> None:
    system = platform.system()
    if system == "Linux":
        filename = f"{APP_NAME}.tar.gz"
    elif system == "Windows":
        filename = f"{APP_NAME}.zip"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    url = f"https://github.com/ShvedovLesha93/quillvox/releases/download/{version}/{filename}"
    archive_path = APP_DIR / filename

    log.info(f"Downloading {version} from: {url}")

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

        log.info(f"Saved to: {archive_path}")
        _extract_and_replace(archive_path)
    finally:
        if archive_path.exists():
            archive_path.unlink()
            log.debug(f"Cleaned up archive: {archive_path}")
    restart_app()


def _extract_and_replace(archive_path: Path) -> None:
    log.info(f"Extracting {archive_path.name} into {APP_DIR}")

    old_exe = APP_DIR / APP_NAME
    backup_exe = APP_DIR / f"{APP_NAME}.old"

    # Rename the running binary — Linux allows this even for a running process
    if old_exe.exists():
        old_exe.rename(backup_exe)
        log.debug(f"Backed up old binary to: {backup_exe}")

    try:
        with tarfile.open(archive_path, "r:gz") as tf:
            members = tf.getmembers()
            log.debug(f"Archive contains {len(members)} files")
            for member in members:
                parts = Path(member.name).parts
                if len(parts) <= 1:
                    continue
                member.name = str(Path(*parts[1:]))
                tf.extract(member, path=APP_DIR, filter="data")
                log.debug(f"Extracted: {member.name}")

        # Restore executable permissions
        if old_exe.exists():
            old_exe.chmod(0o755)

        # Remove backup
        if backup_exe.exists():
            backup_exe.unlink()

        log.info("Extraction complete.")

    except Exception:
        # Roll back on failure
        if backup_exe.exists() and not old_exe.exists():
            backup_exe.rename(old_exe)
            log.error("Extraction failed, restored old binary.")
        raise


def restart_app() -> None:
    """Restarts the app using the new binary."""
    log.info("Restarting app...")
    os.execv(APP_DIR / APP_NAME, [APP_DIR / APP_NAME])


def run(version: str) -> None:
    download_release(version)
