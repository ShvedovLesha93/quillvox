import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, get_args

logger = logging.getLogger(__name__)

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

VadFilterKey = Literal[True, False]


@dataclass(frozen=True)
class STTRunConfig:
    model: str
    device: str
    batch_size: int
    compute_type: str
    language: str
    audio: str


@dataclass
class STTConfig:
    # Parameters for UI
    model: ModelKey = "base"
    device: DeviceKey = "cpu"
    compute_type: ComputeTypeKey = "int8"
    batch_size: BatchSizeKey = 2
    language: LanguageKey = "auto"
    vad_filter: VadFilterKey = False

    # Parameters are not used for UI
    audio: Path | None = field(default=None, metadata={"save": False})

    def as_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "model": self.model,
            "device": self.device,
            "compute_type": self.compute_type,
            "batch_size": self.batch_size,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "STTConfig | None":
        """Deserialize from a plain dict with validation."""
        try:
            model = data.get("model", "base")
            if model not in get_args(ModelKey):
                raise ValueError(
                    f"Invalid 'model' value: {model!r}. Expected one of {get_args(ModelKey)}"
                )

            device = data.get("device", "cpu")
            if device not in get_args(DeviceKey):
                raise ValueError(
                    f"Invalid 'device' value: {device!r}. Expected one of {get_args(DeviceKey)}"
                )

            compute_type = data.get("compute_type", "int8")
            if compute_type not in get_args(ComputeTypeKey):
                raise ValueError(
                    f"Invalid 'compute_type' value: {compute_type!r}. Expected one of {get_args(ComputeTypeKey)}"
                )

            batch_size = data.get("batch_size", 2)
            if batch_size not in get_args(BatchSizeKey):
                raise ValueError(
                    f"Invalid 'batch_size' value: {batch_size!r}. Expected one of {get_args(BatchSizeKey)}"
                )

            language = data.get("language", "auto")
            if language not in get_args(LanguageKey):
                raise ValueError(
                    f"Invalid 'language' value: {language!r}. Expected one of {get_args(LanguageKey)}"
                )

            return cls(
                model=model,
                device=device,
                compute_type=compute_type,
                batch_size=batch_size,
                language=language,
            )
        except ValueError as e:
            logger.error("STT config is corrupted — %s", e)
            return None
