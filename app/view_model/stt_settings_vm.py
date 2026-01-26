from __future__ import annotations
from dataclasses import asdict, fields
from enum import Enum
from typing import TYPE_CHECKING, Dict
from PySide6.QtCore import QObject, Signal, Slot
import copy

from app.constants import SettingsCategory
from app.config.stt_config import (
    ModelKey,
    DeviceKey,
    ComputeTypeKey,
    BatchSizeKey,
    LanguageKey,
)

import logging


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.config.stt_config import STTConfig
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


class STTSettingsViewModel(QObject):
    changed = Signal(object, bool)  # SettingsCategory , bool
    saved = Signal()

    def __init__(self, stt_config: STTConfig, settings_vm: SettingsViewModel) -> None:
        super().__init__()
        self.settings_category = SettingsCategory.STT_SETTINGS
        self.settings_vm = settings_vm
        self._connect_signals()

        self._stt_config = stt_config
        self._snapshot = copy.deepcopy(stt_config)
        self._category_config = {
            STTSettingCategory.MODEL: {
                "attr": "model",
                "labels": MODEL_LABELS,
            },
            STTSettingCategory.DEVICE: {
                "attr": "device",
                "labels": DEVICE_LABELS,
            },
            STTSettingCategory.COMPUTE_TYPE: {
                "attr": "compute_type",
                "labels": COMPUTE_TYPE_LABELS,
            },
            STTSettingCategory.BATCH_SIZE: {
                "attr": "batch_size",
                "labels": BATCH_SIZE_LABELS,
            },
            STTSettingCategory.LANGUAGE: {
                "attr": "language",
                "labels": LANGUAGE_LABELS,
            },
        }

    def _connect_signals(self) -> None:
        self.settings_vm.save_requested.connect(self.save)

    def get_labels(self, category: STTSettingCategory) -> dict:
        config = self._get_config(category)
        labels = config["labels"]
        return labels

    def get_current(self, category: STTSettingCategory) -> str | int:
        config = self._get_config(category)
        attr_name = config["attr"]
        current_value = getattr(self._stt_config, attr_name)
        return current_value

    @Slot()
    def save(self) -> None:
        for field in fields(self._stt_config):
            setattr(self._stt_config, field.name, getattr(self._snapshot, field.name))
        self.saved.emit()

        logger.info("STT settings saved")
        logger.debug("Saved settings %s", asdict(self._stt_config))

    def settings_changed(self, category: STTSettingCategory, key: str) -> None:
        self.set_current(category, key)
        if self._snapshot != self._stt_config:
            self.changed.emit(self.settings_category, True)
        else:
            self.changed.emit(self.settings_category, False)

    def parameter_changed(self, category: STTSettingCategory, key: str) -> bool:
        config = self._get_config(category)
        attr_name = config["attr"]
        current_value = getattr(self._stt_config, attr_name)

        return key != current_value

    def set_current(self, category: STTSettingCategory, key: str) -> None:
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

    def _get_config(self, category: STTSettingCategory) -> dict:
        config = self._category_config.get(category)
        if config is None:
            raise ValueError(f"Invalid category: {category}")
        return config
