from __future__ import annotations
from dataclasses import dataclass
import logging
import sys
from typing import TYPE_CHECKING
from PySide6.QtCore import QProcess, QObject, Signal, Slot

from app.constants import SettingsCategory
from app.view_model.stt_settings_vm import STTSettingsViewModel
from app.view_model.general_settings_vm import GeneralSettingsViewModel

if TYPE_CHECKING:
    from app.config.general_config import GeneralConfig
    from app.config.stt_config import STTConfig
    from app.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class InstallCudaViewModel(QObject):
    install_finished = Signal(bool)  # True = success
    install_output = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._process: QProcess | None = None

    def start_install(self) -> None:
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_output)
        self._process.finished.connect(self._on_finished)
        self._process.start(self._find_uv(), ["sync", "--extra", "cuda"])

    def cancel_install(self) -> None:
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()

    def _find_uv(self) -> str:
        import os
        import shutil
        from pathlib import Path

        launcher_frozen = os.getenv("LAUNCHER_FROZEN") == "1"

        if launcher_frozen:
            base = Path.cwd()
            uv = base / ("uv.exe" if sys.platform == "win32" else "uv")
            logger.debug("uv path: %s", uv)
            if uv.exists():
                return str(uv)

        uv_path = shutil.which("uv") or "uv"
        logger.debug("uv path: %s", uv_path)
        return uv_path

    @Slot()
    def _on_output(self) -> None:
        output = self._process.readAllStandardOutput().data().decode(errors="replace")
        self.install_output.emit(output.strip())

    @Slot(int, QProcess.ExitStatus)
    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self.install_finished.emit(exit_code == 0)


class SettingsViewModel(QObject):
    settings_changed = Signal()
    restore_requested = Signal()
    save_requested = Signal()
    request_torch_cuda = Signal()

    def __init__(
        self,
        stt_config: STTConfig,
        general_config: GeneralConfig,
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__()
        self.install_cuda_vm = InstallCudaViewModel()
        self.stt_config = stt_config
        self.general_config = general_config
        self.theme_manager = theme_manager
        self._is_changed: dict[SettingsCategory, bool] = {
            SettingsCategory.GENERAL: False,
            SettingsCategory.STT: False,
        }

        self.general_settings_vm = GeneralSettingsViewModel(
            general_config=self.general_config,
            theme_manager=self.theme_manager,
            settings_vm=self,
        )
        self.stt_settings_vm = STTSettingsViewModel(
            stt_config=self.stt_config, settings_vm=self
        )
        self._connect_signals()

    def has_any_changes(self) -> bool:
        return any(self._is_changed.values())

    def has_category_changes(self, category: SettingsCategory) -> bool:
        return self._is_changed[category]

    def _on_settings_changed(self, category: SettingsCategory, state: bool) -> None:
        self._is_changed[category] = state
        self.settings_changed.emit()

    def _connect_signals(self) -> None:
        settings = (self.stt_settings_vm.changed, self.general_settings_vm.changed)
        for signal in settings:
            signal.connect(self._on_settings_changed)
