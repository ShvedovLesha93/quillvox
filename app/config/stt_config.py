from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ModelKey = Literal[
    "tiny",
    "base",
    "small",
    "medium",
    "large",
    "turbo",
]

DeviceKey = Literal[
    "cpu",
    "cuda",
]

ComputeTypeKey = Literal[
    "float16",
    "float32",
    "int8",
    "int8_float16",
]

BatchSizeKey = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

LanguageKey = Literal[
    "auto",
    "en",
    "fr",
    "de",
    "es",
    "it",
    "ja",
    "zh",
    "nl",
    "uk",
    "pt",
    "ar",
    "ru",
    "pl",
    "hu",
    "fi",
    "fa",
    "el",
    "tr",
]


@dataclass
class STTConfig:

    model: ModelKey = "base"
    device: DeviceKey = "cpu"
    compute_type: ComputeTypeKey = "int8"
    batch_size: BatchSizeKey = 2
    language: LanguageKey = "auto"
    audio: Path | None = None

    def as_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "model": self.model,
            "device": self.device,
            "compute_type": self.compute_type,
            "batch_size": self.batch_size,
            "language": self.language,
            "audio": self.audio,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "STTConfig":
        """Deserialize from a plain dict with validation."""
        return cls(
            model=data.get("model", "base"),
            device=data.get("device", "cpu"),
            compute_type=data.get("compute_type", "int8"),
            batch_size=data.get("batch_size", 2),
            language=data.get("language", "auto"),
            audio=data.get("audio", None),
        )
