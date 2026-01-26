from dataclasses import dataclass
from typing import Literal

from app.constants import ThemeMode

InterfaceLanguageKey = Literal["en", "ru"]
ThemeKey = Literal[ThemeMode.SYSTEM, ThemeMode.DARK, ThemeMode.LIGHT]


@dataclass
class GeneralConfig:

    language: InterfaceLanguageKey = "ru"
    theme: ThemeKey = ThemeMode.SYSTEM

    def as_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {"language": self.language, "theme": self.theme}

    @classmethod
    def from_dict(cls, data: dict) -> "GeneralConfig":
        """Deserialize from a plain dict with validation."""
        return cls(
            language=data.get("language", "auto"),
            theme=data.get("theme", ThemeMode.SYSTEM),
        )
