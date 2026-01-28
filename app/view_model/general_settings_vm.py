from __future__ import annotations
import copy
from dataclasses import asdict, dataclass, fields
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, TypeVar

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

K = TypeVar("K")


@dataclass
class CategoryConfig(Generic[K]):
    atr_name: str
    labels: Dict[K, str]
    on_change: Callable[[Any], None] | None = None


class GeneralSettingsViewModel(QObject):
    changed = Signal(object, bool)  # SettingsCategory, bool
    discarded = Signal()
    saved = Signal()

    def __init__(
        self,
        general_config: GeneralConfig,
        settings_vm: SettingsViewModel,
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__()
        self.settings_vm = settings_vm
        self.theme_manager = theme_manager

        # Saved configuration
        self._config = general_config

        # For unsaved changes
        self._snapshot = copy.deepcopy(self._config)

        self._categories = self._build_category_config()

        self._connect_signals()

    def _build_category_config(self) -> Dict[GeneralSettingCategory, CategoryConfig]:

        return {
            GeneralSettingCategory.LANGUAGE: CategoryConfig(
                atr_name="language",
                labels=LANGUAGE_LABELS,
                on_change=self.apply_language,
            ),
            GeneralSettingCategory.THEME: CategoryConfig(
                atr_name="theme", labels=THEME_LABELS, on_change=self.apply_theme
            ),
        }

    def _connect_signals(self) -> None:
        self.settings_vm.save_requested.connect(self.save)
        self.settings_vm.restore_requested.connect(self.discard)

    @Slot(object)
    def get_labels(self, category: GeneralSettingCategory) -> dict:
        config = self._get_config(category)
        return config.labels

    @Slot(object)
    def get_current_value(self, category: GeneralSettingCategory) -> str | ThemeMode:
        """Get the currently saved value (not including unsaved changes)"""
        config = self._get_config(category)
        return getattr(self._config, config.atr_name)

    # ============ Change Handling ============

    @Slot(object, object)
    def on_value_changed(
        self, category: GeneralSettingCategory, new_value: str | ThemeMode
    ) -> bool:
        self.on_setting_changed(category, new_value)
        self.preview_change(category, new_value)
        return self.value_has_change(category, new_value)

    def on_setting_changed(
        self, category: GeneralSettingCategory, value: str | ThemeMode
    ) -> None:
        self._update_snapshot(category, value)
        self._emit_change_status()

    def preview_change(
        self, category: GeneralSettingCategory, new_value: str | ThemeMode
    ) -> None:
        """
        Apply a change immediately for preview it before saving.
        This allows users to see the effect of their changes before saving them.
        """
        config = self._get_config(category)

        if config.on_change:
            config.on_change(new_value)

    def value_has_change(
        self, category: GeneralSettingCategory, value: str | ThemeMode
    ) -> bool:
        """Check if a value differs from the currently saved config"""
        current_saved = self.get_current_value(category)
        return value != current_saved

    def has_unsaved_changes(self) -> bool:
        return self._snapshot != self._config

    # ============ Save/Reset ============

    @Slot()
    def save(self) -> None:
        for field in fields(self._config):
            snapshot_value = getattr(self._snapshot, field.name)
            setattr(self._config, field.name, snapshot_value)
        self.saved.emit()
        self._emit_change_status()

        logger.info("General settings saved: %s", asdict(self._config))

    def discard(self) -> None:
        self._snapshot = copy.deepcopy(self._config)
        self.discarded.emit()
        self._emit_change_status()

    # ============ Internal Helpers ============

    def _get_config(self, category: GeneralSettingCategory) -> CategoryConfig:
        config = self._categories.get(category)
        if config is None:
            raise ValueError(f"Unknow category: {category}")
        return config

    def _update_snapshot(
        self, category: GeneralSettingCategory, new_value: str | ThemeMode
    ) -> None:
        config = self._get_config(category)

        if new_value not in config.labels:
            raise ValueError(
                f"Invalid value '{new_value} for {category.value}"
                f"Allowed: {list(config.labels.keys())}"
            )

        # Only updates if value changed
        current_value = getattr(self._snapshot, config.atr_name)
        if new_value != current_value:
            setattr(self._snapshot, config.atr_name, new_value)
            logger.debug("Updated snapshot %s: %s", category.value, new_value)

    def _emit_change_status(self) -> None:
        has_changed = self.has_unsaved_changes()
        self.changed.emit(SettingsCategory.GENERAL, has_changed)

    # ============ Apply setting ============

    def apply_language(self, value: str) -> None:
        language_manager.set_language(value)

    def apply_theme(self, value: ThemeKey) -> None:
        self.theme_manager.set_theme(value)
