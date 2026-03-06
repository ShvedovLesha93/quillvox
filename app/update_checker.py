import json
import requests
from packaging import version
from PySide6.QtCore import QObject, QThread, Signal
from enum import IntEnum

from app.translator import _


class UpdateStatus(IntEnum):
    NO_UPDATE = 0
    UPDATE_AVAILABLE = 1
    ERROR = 2


status = UpdateStatus.UPDATE_AVAILABLE


class UpdateCheckerWorker(QThread):
    """Check for updates in background thread."""

    # Signals
    update_available = Signal(str)  # Emits latest version
    no_update = Signal()
    error_occurred = Signal(str)  # Emits error message
    finished = Signal()

    def __init__(self, current_version: str, update_url: str):
        super().__init__()
        self.current_version = current_version
        self.update_url = update_url

    def run(self):
        """Run update check in background."""
        try:
            # Fetch latest version info
            response = requests.get(self.update_url, timeout=5)
            response.raise_for_status()

            data = response.json()
            latest = data.get("version", None)

            if not latest:
                self.error_occurred.emit(_("No version found in response"))
                return

            # Compare versions
            if version.parse(latest) > version.parse(self.current_version):
                self.update_available.emit(latest)
            else:
                self.no_update.emit()

        except requests.RequestException as e:
            self.error_occurred.emit(_(f"Network error: {e}").format(e=str(e)))
        except json.JSONDecodeError as e:
            self.error_occurred.emit(_(f"Invalid JSON: {e}").format(e=str(e)))
        except Exception as e:
            self.error_occurred.emit(_(f"Unexpected error: {e}").format(e=str(e)))

        finally:
            self.finished.emit()


class UpdateChecker(QObject):
    message = Signal(UpdateStatus, str, str)

    def __init__(self) -> None:
        super().__init__()
        self._first_run = True
        self.url = "https://raw.githubusercontent.com/ShvedovLesha93/quillvox/refs/heads/main/version.json"
        self._current_version = None

    @property
    def current_version(self) -> str:
        # Load current version
        with open("version.json", "r", encoding="utf-8") as v:
            current_dict = json.loads(v.read())
            return current_dict.get("version", "0.0.0")

    def check_for_updates(self):
        """Start update check."""
        if not self._current_version:
            self._current_version = self.current_version

        self.update_checker = UpdateCheckerWorker(self._current_version, self.url)

        # Connect signals
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.no_update.connect(self.on_no_update)
        self.update_checker.error_occurred.connect(self.on_error)

        # Start checking
        self.update_checker.start()

    def on_update_available(self, latest_version: str):
        self.message.emit(
            UpdateStatus.UPDATE_AVAILABLE,
            _("Update available: {current} → {latest}").format(
                current=self._current_version, latest=latest_version
            ),
            latest_version,
        )

    def on_no_update(self):
        if self._first_run:
            # Skip sending message on first run
            self._first_run = False
            return
        self.message.emit(UpdateStatus.NO_UPDATE, _("You're up to date!"), "")

    def on_error(self, error_msg: str):
        self.message.emit(
            UpdateStatus.ERROR,
            _("Update check failed: {error_msg}").format(error_msg=error_msg),
            "",
        )
