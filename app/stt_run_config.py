from dataclasses import dataclass


@dataclass(frozen=True)
class STTRunConfig:
    model: str
    device: str
    batch_size: int
    compute_type: str
    language: str
    audio: str
