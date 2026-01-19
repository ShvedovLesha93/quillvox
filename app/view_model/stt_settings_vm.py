from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING, Dict
from PySide6.QtCore import QObject

from app.models.stt_config import (
    ModelKey,
    DeviceKey,
    ComputeTypeKey,
    BatchSizeKey,
    LanguageKey,
)

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.models.stt_config import STTConfig


class Category(Enum):
    MODEL = ("model",)
    DEVICE = ("device",)
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

    def __init__(self, stt_config: STTConfig) -> None:
        super().__init__()
        self._stt_config = stt_config

    def get_labels(self, category: Category) -> dict:
        match category:
            case Category.MODEL:
                return MODEL_LABELS
            case Category.DEVICE:
                return DEVICE_LABELS
            case Category.COMPUTE_TYPE:
                return COMPUTE_TYPE_LABELS
            case Category.BATCH_SIZE:
                return BATCH_SIZE_LABELS
            case Category.LANGUAGE:
                return LANGUAGE_LABELS

    def get_current(self, category: Category) -> str | int:
        match category:
            case Category.MODEL:
                return self._stt_config.model
            case Category.DEVICE:
                return self._stt_config.device
            case Category.COMPUTE_TYPE:
                return self._stt_config.compute_type
            case Category.BATCH_SIZE:
                return self._stt_config.batch_size
            case Category.LANGUAGE:
                return self._stt_config.language

    def set_current(self, category: Category, key: str) -> None:
        match category:
            case Category.MODEL:
                if key != self._stt_config.model:
                    if key not in MODEL_LABELS:
                        raise ValueError(f"Invalid model key: {key}")
                    self._stt_config.model = key
                    logger.debug("set %s: %s", Category.MODEL, key)
            case Category.DEVICE:
                if key != self._stt_config.device:
                    if key not in DEVICE_LABELS:
                        raise ValueError(f"Invalid device key: {key}")
                    self._stt_config.device = key
                    logger.debug("set %s: %s", Category.DEVICE, key)
            case Category.COMPUTE_TYPE:
                if key != self._stt_config.compute_type:
                    if key not in COMPUTE_TYPE_LABELS:
                        raise ValueError(f"Invalid compute_type key: {key}")
                    self._stt_config.compute_type = key
                    logger.debug("set %s: %s", Category.COMPUTE_TYPE, key)
            case Category.BATCH_SIZE:
                if key != self._stt_config.batch_size:
                    if key not in BATCH_SIZE_LABELS:
                        raise ValueError(f"Invalid batch_size key: {key}")
                    self._stt_config.batch_size = key
                    logger.debug("set %s: %s", Category.BATCH_SIZE, key)
            case Category.LANGUAGE:
                if key != self._stt_config.language:
                    if key not in LANGUAGE_LABELS:
                        raise ValueError(f"Invalid language key: {key}")
                    self._stt_config.language = key
                    logger.debug("set %s: %s", Category.LANGUAGE, key)
