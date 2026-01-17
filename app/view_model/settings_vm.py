from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from app.translator import _, language_manager

from app.constants import ThemeMode

if TYPE_CHECKING:
    from app.theme_manager import ThemeManager

import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Language:
    code: str
    translated: str
    native: str


@dataclass(frozen=True)
class Theme:
    data: ThemeMode
    translated: str


class SettingsViewModel(QObject):
    language_changed = Signal(str)

    def __init__(self, theme_manager: ThemeManager) -> None:
        super().__init__()
        self.theme_manager = theme_manager

        self._languages: list[Language] = []
        self._themes: list[Theme] = []

        self._current_language: str = language_manager.current_lang
        self._current_theme = self.theme_manager.applied_theme

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def retranslate(self) -> None:
        self._languages = [
            Language(code="en", translated=_("English"), native="English"),
            Language(code="ru", translated=_("Russian"), native="Русский"),
        ]
        self._themes = [
            Theme(data=ThemeMode.DARK, translated=_("Dark")),
            Theme(data=ThemeMode.LIGHT, translated=_("Light")),
            Theme(data=ThemeMode.SYSTEM, translated=_("System")),
        ]

    @property
    def themes(self) -> list[Theme]:
        return self._themes

    @property
    def current_theme(self) -> ThemeMode:
        return self._current_theme

    @property
    def languages(self) -> list[Language]:
        """Return available languages as (code, label)."""
        return self._languages

    @property
    def current_language(self) -> str:
        return self._current_language

    def set_language(self, code: str) -> None:
        if code == self._current_language:
            return

        self._current_language = code
        self.language_changed.emit(code)

    def set_theme(self, theme: ThemeMode) -> None:
        self.theme_manager.set_theme(theme)

        logger.info("Theme changed by user: %s", theme)
