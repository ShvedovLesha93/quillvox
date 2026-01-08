from __future__ import annotations
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal
from app.translator import _, language_manager


@dataclass(frozen=True)
class Language:
    code: str
    translated: str
    native: str


class SettingsVM(QObject):
    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._languages: list[Language] = []

        self._current_language: str = language_manager.current_lang

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def retranslate(self) -> None:
        self._languages = [
            Language(code="en", translated=_("English"), native="English"),
            Language(code="ru", translated=_("Russian"), native="Русский"),
        ]

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
