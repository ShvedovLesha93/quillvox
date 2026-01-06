from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class SettingsVM(QObject):
    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._languages: list[tuple[str, str]] = [
            ("en", "English"),
            ("ru", "Russian"),
        ]

        self._current_language: str = ""

    def languages(self) -> list[tuple[str, str]]:
        """Return available languages as (code, label)."""
        return self._languages

    def on_combo_changed(self, label: str) -> None:
        """
        Called when the combo text changes.
        Maps UI label back to language code.
        """
        for code, text in self._languages:
            if text == label:
                self.set_language(code)
                return

    def set_language(self, code: str) -> None:
        if code == self._current_language:
            return

        self._current_language = code
        self.language_changed.emit(code)
