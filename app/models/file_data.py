from dataclasses import dataclass, field


@dataclass
class SupportedFormats:
    audio: list[str] = field(
        default_factory=lambda: [
            "*.mp3",
            "*.wav",
            "*.ogg",
            "*.flac",
            "*.m4a",
        ]  # TODO: Maybe switch to list? 2026-01-28 09:37
    )
    video: list[str] = field(
        default_factory=lambda: [
            "*.mp4",
            "*.mkv",
            "*.avi",
            "*.mov",
            "*.flv",
            "*.webm",
            "*.wmv",
            "*.m4v",
        ]
    )
