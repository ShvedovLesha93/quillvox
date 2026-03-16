import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, get_args

from app.utils import cuda_checker

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
    language: LanguageKey = "auto"
    vad_filter: VadFilterKey = False
    is_cuda_supported: bool = field(
        default_factory=lambda: cuda_checker.has_cuda_support()
    )
    is_cuda_installed: bool = field(
        default_factory=lambda: cuda_checker.has_nvidia_libs_installed()
    )

    # Parameters are not used for UI
    audio: Path | None = field(default=None, metadata={"save": False})

    def as_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "model": self.model,
            "device": self.device,
            "compute_type": self.compute_type,
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

            language = data.get("language", "auto")
            if language not in get_args(LanguageKey):
                raise ValueError(
                    f"Invalid 'language' value: {language!r}. Expected one of {get_args(LanguageKey)}"
                )

            return cls(
                model=model,
                device=device,
                compute_type=compute_type,
                language=language,
            )
        except ValueError as e:
            logger.error("STT config is corrupted — %s", e)
            return None
