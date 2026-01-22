from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

from app.view_model.general_settings_vm import GeneralSettingsViewModel
from app.view_model.stt_settings_vm import STTSettingsViewModel

if TYPE_CHECKING:
    from app.models.stt_config import STTConfig
    from app.theme_manager import ThemeManager


class SettingsViewModel(QObject):
    settings_changed = Signal(object)  # SettingsCategory
    settings_restored = Signal(object)  # SettingsCategory
    restore_requested = Signal()
    save_requested = Signal()

    def __init__(self, stt_config: STTConfig, theme_manager: ThemeManager) -> None:
        super().__init__()
        self.stt_config = stt_config
        self.theme_manager = theme_manager

        self.general_settings_vm = GeneralSettingsViewModel(self.theme_manager)
        self.stt_settings_vm = STTSettingsViewModel(
            stt_config=self.stt_config, settings_vm=self
        )
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.stt_settings_vm.changed.connect(self.settings_changed.emit)
        self.stt_settings_vm.restored.connect(self.settings_restored.emit)
