from enum import Enum, auto


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
    STT_SETTINGS = auto()
    GENERAL_SETTINGS = auto()
