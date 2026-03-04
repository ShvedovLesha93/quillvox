from __future__ import annotations
from dataclasses import asdict, dataclass, fields
from enum import Enum
from typing import TYPE_CHECKING, Dict, Generic, TypeVar
from PySide6.QtCore import QObject, Signal, Slot

from app.config import config_manager
from app.constants import SettingsCategory
from app.config.stt_config import (
    ModelKey,
    DeviceKey,
    ComputeTypeKey,
    BatchSizeKey,
    LanguageKey,
)

import logging
from app.config.stt_config import STTConfig

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.view_model.settings_vm import SettingsViewModel


class STTSettingCategory(Enum):
    MODEL = "model"
    DEVICE = "device"
    COMPUTE_TYPE = "compute_type"
    BATCH_SIZE = "batch_size"
    LANGUAGE = "language"


MODEL_LABELS: Dict[ModelKey, str] = {
    "tiny": "Tiny",
    "base": "Base",
    "small": "Small",
    "medium": "Medium",
    "large": "Large",
    "turbo": "Turbo",
}

DEVICE_LABELS: Dict[DeviceKey, str] = {
    "cpu": "CPU",
    "cuda": "CUDA",
}

COMPUTE_TYPE_LABELS: Dict[ComputeTypeKey, str] = {
    "float16": "Float16",
    "float32": "Float32",
    "int8": "Int8",
    "int8_float16": "Int8 Float16",
}

BATCH_SIZE_LABELS: Dict[BatchSizeKey, str] = {
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "10",
    11: "11",
    12: "12",
    13: "13",
    14: "14",
    15: "15",
    16: "16",
    17: "17",
}

LANGUAGE_LABELS: Dict[LanguageKey, str] = {
    "auto": "Auto",
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "ja": "Japanese",
    "zh": "Chinese",
    "nl": "Dutch",
    "uk": "Ukrainian",
    "pt": "Portuguese",
    "ar": "Arabic",
    "ru": "Russian",
    "pl": "Polish",
    "hu": "Hungarian",
    "fi": "Finnish",
    "fa": "Persian",
    "el": "Greek",
    "tr": "Turkish",
}

K = TypeVar("K")


@dataclass()
class CategoryConfig(Generic[K]):
    atr_name: str
    labels: Dict[K, str]


class STTSettingsViewModel(QObject):
    changed = Signal(object, bool)  # SettingsCategory , bool
    discarded = Signal()
    saved = Signal()

    def __init__(self, stt_config: STTConfig, settings_vm: SettingsViewModel) -> None:
        super().__init__()
        self.settings_vm = settings_vm

        # Saved configuration
        self._config = stt_config

        # For unsaved changes
        self._snapshot = self._make_shapshot()

        self._categories = self._build_category_config()

        self._connect_signals()

    def _make_shapshot(self) -> STTConfig:
        snapshot = STTConfig()

        for field in fields(self._config):
            if not field.metadata.get("save", True):
                continue

            snapshot_value = getattr(self._config, field.name)
            setattr(snapshot, field.name, snapshot_value)

        logger.debug("Gerenated snapshot: %s", snapshot)

        return snapshot

    def _build_category_config(self) -> Dict[STTSettingCategory, CategoryConfig]:

        return {
            STTSettingCategory.MODEL: CategoryConfig(
                atr_name="model", labels=MODEL_LABELS
            ),
            STTSettingCategory.DEVICE: CategoryConfig(
                atr_name="device", labels=DEVICE_LABELS
            ),
            STTSettingCategory.COMPUTE_TYPE: CategoryConfig(
                atr_name="compute_type", labels=COMPUTE_TYPE_LABELS
            ),
            STTSettingCategory.BATCH_SIZE: CategoryConfig(
                atr_name="batch_size", labels=BATCH_SIZE_LABELS
            ),
            STTSettingCategory.LANGUAGE: CategoryConfig(
                atr_name="language", labels=LANGUAGE_LABELS
            ),
        }

    def _connect_signals(self) -> None:
        self.settings_vm.save_requested.connect(self.save)
        self.settings_vm.restore_requested.connect(self.discard)

    @Slot(object)
    def get_labels(self, category: STTSettingCategory) -> dict:
        config = self._get_config(category)
        return config.labels

    @Slot(object)
    def get_current_value(self, category: STTSettingCategory) -> str | int:
        """Get the currently saved value (not including unsaved changes)"""
        config = self._get_config(category)
        return getattr(self._config, config.atr_name)

    # ============ Change Handling ============

    @Slot(object, object)
    def on_value_changed(
        self, category: STTSettingCategory, new_value: str | int
    ) -> bool:
        self.on_setting_changed(category, new_value)
        return self.value_has_change(category, new_value)

    def on_setting_changed(
        self, category: STTSettingCategory, value: str | int
    ) -> None:
        self._update_snapshot(category, value)
        self._emit_change_status()

    def value_has_change(self, category: STTSettingCategory, value: str | int) -> bool:
        """Check if a value differs from the currently saved config"""
        current_saved = self.get_current_value(category)
        return value != current_saved

    def has_unsaved_changes(self) -> bool:
        for f in fields(self._config):
            if not f.metadata.get("save", True):
                continue

            if getattr(self._snapshot, f.name) != getattr(self._config, f.name):
                return True

        return False

    # ============ Save/Reset ============

    @Slot()
    def save(self) -> None:
        for field in fields(self._config):
            if not field.metadata.get("save", True):
                continue

            snapshot_value = getattr(self._snapshot, field.name)
            setattr(self._config, field.name, snapshot_value)

        self.saved.emit()
        self._emit_change_status()
        config_manager.save_stt_config(self._config.as_dict())

        logger.info("General settings saved: %s", asdict(self._config))

    def discard(self) -> None:
        self._snapshot = self._make_shapshot()
        self.discarded.emit()
        self._emit_change_status()

    # ============ Internal Helpers ============

    def _get_config(self, category: STTSettingCategory) -> CategoryConfig:
        config = self._categories.get(category)
        if config is None:
            raise ValueError(f"Unknow category: {category}")
        return config

    def _update_snapshot(
        self, category: STTSettingCategory, new_value: str | int
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
        self.changed.emit(SettingsCategory.STT, has_changed)
