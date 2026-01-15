from dataclasses import dataclass, field
from typing import Dict, Generic, Optional, TypeVar


@dataclass
class Value:
    label: str


@dataclass
class ModelValue(Value):
    is_downloaded: bool = False
    size: Optional[int | float] = None


K = TypeVar("K")
V = TypeVar("V", bound=Value)


class Parameter(Generic[K, V]):
    def __init__(self, label: str, current: K, values: Dict[K, V]) -> None:
        self.label = label
        self.values = values
        self._current = current

    def __post_init__(self):
        self._check_current()

    def _check_current(self, current=None):
        if current is None:
            current = self._current

        params = self.values.keys()

        if current not in params:
            raise ValueError(f"'{current}' not in {list(params)}")

    @property
    def current(self) -> K:
        return self._current

    @current.setter
    def current(self, value: K) -> None:
        self._check_current(value)
        self._current = value


@dataclass
class STTConfig:
    model: Parameter[str, ModelValue] = field(
        default_factory=lambda: Parameter(
            label="Model",
            current="base",
            values={
                "tiny": ModelValue(label="Tiny"),
                "base": ModelValue(label="Base"),
                "small": ModelValue(label="Small"),
                "medium": ModelValue(label="Medium"),
                "large": ModelValue(label="Large"),
                "turbo": ModelValue(label="Turbo"),
            },
        )
    )
    device: Parameter[str, Value] = field(
        default_factory=lambda: Parameter(
            label="Device",
            current="cpu",
            values={
                "cpu": Value(label="CPU"),
                "cuda": Value(label="CUDA"),
            },
        )
    )
    compute_type: Parameter[str, Value] = field(
        default_factory=lambda: Parameter(
            label="Compute type",
            current="int8",
            values={
                "float16": Value(label="Float16"),
                "float32": Value(label="Float32"),
                "int8": Value(label="Int8"),
                "int8_float16": Value(label="Int8 and float16"),
            },
        )
    )
    batch_size: Parameter[int, Value] = field(
        default_factory=lambda: Parameter(
            label="Batch size",
            current=2,
            values={i: Value(label=str(i)) for i in range(1, 17)},
        )
    )
    language: Parameter[str, Value] = field(
        default_factory=lambda: Parameter(
            label="Language",
            current="ru",
            values={
                "auto": Value(label="Auto"),
                "en": Value(label="English"),
                "fr": Value(label="French"),
                "de": Value(label="German"),
                "es": Value(label="Spanish"),
                "it": Value(label="Italian"),
                "ja": Value(label="Japanese"),
                "zh": Value(label="Chinese"),
                "nl": Value(label="Dutch"),
                "uk": Value(label="Ukrainian"),
                "pt": Value(label="Portuguese"),
                "ar": Value(label="Arabic"),
                "ru": Value(label="Russian"),
                "pl": Value(label="Polish"),
                "hu": Value(label="Hungarian"),
                "fi": Value(label="Finnish"),
                "fa": Value(label="Persian"),
                "el": Value(label="Greek"),
                "tr": Value(label="Turkish"),
            },
        )
    )
