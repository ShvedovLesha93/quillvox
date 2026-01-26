from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal, Slot

from app.constants import SettingsCategory
from app.view_model.stt_settings_vm import STTSettingsViewModel
from app.view_model.general_settings_vm import GeneralSettingsViewModel

if TYPE_CHECKING:
    from app.config.general_config import GeneralConfig
    from app.config.stt_config import STTConfig
    from app.theme_manager import ThemeManager


class SettingsViewModel(QObject):
    settings_changed = Signal(object, bool)  # SettingsCategory, bool
    # settings_restored = Signal(object)  # SettingsCategory
    restore_requested = Signal()
    save_requested = Signal()

    def __init__(
        self,
        stt_config: STTConfig,
        general_config: GeneralConfig,
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__()
        self.stt_config = stt_config
        self.general_config = general_config
        self.theme_manager = theme_manager

        self.general_settings_vm = GeneralSettingsViewModel(
            general_config=self.general_config,
            theme_manager=self.theme_manager,
            settings_vm=self,
        )
        self.stt_settings_vm = STTSettingsViewModel(
            stt_config=self.stt_config, settings_vm=self
        )
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.stt_settings_vm.changed.connect(self.settings_changed.emit)
        self.general_settings_vm.changed.connect(self.settings_changed.emit)
