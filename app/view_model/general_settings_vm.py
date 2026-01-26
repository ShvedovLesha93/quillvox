from __future__ import annotations
import copy
from dataclasses import asdict, fields
from enum import Enum
from typing import TYPE_CHECKING, Dict

from PySide6.QtCore import QObject, Signal, Slot
from app.translator import language_manager

from app.constants import SettingsCategory, ThemeMode
from app.config.general_config import InterfaceLanguageKey, ThemeKey

if TYPE_CHECKING:
    from app.view_model.settings_vm import SettingsViewModel
    from app.config.general_config import GeneralConfig
    from app.theme_manager import ThemeManager

import logging

logger = logging.getLogger(__name__)


class GeneralSettingCategory(Enum):
    LANGUAGE = "language"
    THEME = "theme"


LANGUAGE_LABELS: Dict[InterfaceLanguageKey, str] = {"ru": "Русский", "en": "English"}

THEME_LABELS: Dict[ThemeKey, str] = {
    ThemeMode.SYSTEM: "System",
    ThemeMode.DARK: "Dark",
    ThemeMode.LIGHT: "Light",
}


class GeneralSettingsViewModel(QObject):
    changed = Signal(object, bool)  # SettingsCategory, bool
    saved = Signal()

    def __init__(
        self,
        general_config: GeneralConfig,
        settings_vm: SettingsViewModel,
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__()
        self.settings_vm = settings_vm
        self._connect_signals()

        self._general_config = general_config
        self._snapshot = copy.deepcopy(self._general_config)
        self.theme_manager = theme_manager
        self._category_config = {
            GeneralSettingCategory.LANGUAGE: {
                "attr": "language",
                "labels": LANGUAGE_LABELS,
            },
            GeneralSettingCategory.THEME: {
                "attr": "theme",
                "labels": THEME_LABELS,
            },
        }

        # language_manager.set_language(self.general_config.language)
        # TODO: 2026-01-23 14:50
        """
        The language should be set when the user selects a language in the settings.
        The first theme that is initialized is the System theme.
        """
        self._current_language: str = language_manager.current_lang
        # self._current_theme = self.theme_manager.applied_theme

    def _connect_signals(self) -> None:
        self.settings_vm.save_requested.connect(self.save)

    def get_labels(self, category: GeneralSettingCategory) -> dict:
        config = self._get_config(category)
        labels = config["labels"]
        return labels

    def get_current(self, category: GeneralSettingCategory) -> str | int:
        config = self._get_config(category)
        attr_name = config["attr"]
        current_value = getattr(self._general_config, attr_name)
        return current_value

    @Slot()
    def save(self) -> None:
        for field in fields(self._general_config):
            setattr(
                self._general_config, field.name, getattr(self._snapshot, field.name)
            )
        self.saved.emit()

        logger.info("General settings saved")
        logger.debug("Saved settings %s", asdict(self._general_config))

    def settings_changed(self, category: GeneralSettingCategory, key: str) -> None:
        self.set_current(category, key)
        if self._snapshot != self._general_config:
            self.changed.emit(SettingsCategory.GENERAL_SETTINGS, True)
        else:
            self.changed.emit(SettingsCategory.GENERAL_SETTINGS, False)

    def parameter_changed(self, category: GeneralSettingCategory, key) -> bool:
        config = self._get_config(category)
        attr_name = config["attr"]
        current_value = getattr(self._general_config, attr_name)

        return key != current_value

    def _on_language_changed(self, key: str) -> None:
        language_manager.set_language(key)

    def _on_theme_chenged(self, key: ThemeKey) -> None:
        self.theme_manager.set_theme(key)

    def set_current(self, category: GeneralSettingCategory, key: str) -> None:
        match category:
            case GeneralSettingCategory.LANGUAGE:
                self._on_language_changed(key)
            case GeneralSettingCategory.THEME:
                self._on_theme_chenged(key)

        config = self._category_config.get(category)
        if config is None:
            raise ValueError(f"Invalid category: {category}")

        attr_name = config["attr"]
        current_value = getattr(self._snapshot, attr_name)

        if key != current_value:
            if key not in config["labels"]:
                raise ValueError(f"Invalid {attr_name} key: {key}")
            setattr(self._snapshot, attr_name, key)
            logger.debug("set %s: %s", category, key)

    def _get_config(self, category: GeneralSettingCategory) -> dict:
        config = self._category_config.get(category)
        if config is None:
            raise ValueError(f"Invalid category: {category}")
        return config
