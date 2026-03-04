from dataclasses import dataclass
import logging
from typing import Literal, get_args

from app.constants import ThemeMode

InterfaceLanguageKey = Literal["en", "ru"]
ThemeKey = Literal[ThemeMode.SYSTEM, ThemeMode.DARK, ThemeMode.LIGHT]


logger = logging.getLogger(__name__)


@dataclass
class GeneralConfig:
    language: InterfaceLanguageKey = "ru"
    theme: ThemeKey = ThemeMode.SYSTEM

    def as_dict(self) -> dict:
        return {"language": self.language, "theme": self.theme.value}  # store int

    @classmethod
    def from_dict(cls, data: dict) -> "GeneralConfig | None":
        try:
            language = data.get("language", "en")
            if language not in get_args(InterfaceLanguageKey):
                raise ValueError(
                    f"Invalid 'language' value: {language!r}. Expected one of {get_args(InterfaceLanguageKey)}"
                )

            theme_value = data.get("theme", ThemeMode.SYSTEM.value)
            try:
                theme = ThemeMode(theme_value)  # int → ThemeMode
            except ValueError:
                raise ValueError(
                    f"Invalid 'theme' value: {theme_value!r}. Expected one of {[m.value for m in ThemeMode]}"
                )

            return cls(language=language, theme=theme)  # pyright: ignore

        except ValueError as e:
            logger.error("General config is corrupted — %s", e)
            return None
