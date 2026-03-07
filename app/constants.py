from enum import Enum, auto


class BuildConfig(Enum):
    UV_VERSION = "0.10.4"


class SubtitleFormat(Enum):
    SRT = "srt"
    VTT = "vtt"
    TXT = "txt"


class PlaybackState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    SEEKING = auto()
    END_SEEKING = auto()


class ThemeMode(Enum):
    LIGHT = 0
    DARK = 1
    SYSTEM = 2


class SettingsCategory(Enum):
    STT = "stt"
    GENERAL = "general"
