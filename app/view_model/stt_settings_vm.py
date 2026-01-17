from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from app.models.stt_config import STTConfig


class parameter(Enum):
    MODEL = "model"
    DEVICE = "device"


@dataclass(frozen=True)
class STTConfigView:
    label: str
    current: str | int
    params: dict


class STTSettingsViewModel(QObject):
    language_changed = Signal(str)

    def __init__(self, stt_config: STTConfig) -> None:
        super().__init__()
        self.stt_config = stt_config

    def get_model_config(self) -> STTConfigView:
        label = self.stt_config.model.label
        current = self.stt_config.model.current
        params = {}
        for key, val in self.stt_config.model.values.items():
            params[key] = val.label

        return STTConfigView(label=label, current=current, params=params)

    def get_configs(self, parameter):
        if parameter == "model":
            pass
