import gettext
from pathlib import Path
import sys

from PySide6.QtCore import QObject, Signal

import logging

from app.constants import FrozenPath

logger = logging.getLogger(__name__)


class LanguageManager(QObject):
    language_changed = Signal()

    def __init__(self):
        super().__init__()

        # Detect if running from PyInstaller bundle
        if getattr(sys, "frozen", False):
            self.locales_dir = Path(FrozenPath.LOCALES.value)
        else:
            # Running in normal Python environment
            self.locales_dir = Path("app/locales")

        logger.info(f"Locales directory: {self.locales_dir}")

        self._ = None
        self.translator = None

    def _is_language_avilable(self, lang_code: str) -> bool:
        """Check if a language has translation files available"""

        mo_file = self.locales_dir / lang_code / "LC_MESSAGES" / "messages.mo"
        return mo_file.exists()

    def get_available_languages(self) -> list[str]:
        """Get list of all available language codes"""
        available = []
        if not self.locales_dir.exists():
            logger.warning("Locales directory does not extst: %s", self.locales_dir)
            return available

        for lang_dir in self.locales_dir.iterdir():
            if lang_dir.is_dir():
                mo_file = lang_dir / "LC_MESSAGES" / "messages.po"
                if mo_file.exists():
                    code = mo_file.parent.parent.name
                    available.append(code)

        return sorted(available)

    def set_language(self, lang_code: str) -> None:
        """Set the application language"""
        if not self._is_language_avilable(lang_code) and lang_code != "en":
            logger.warning(
                "Language '%s' not found. Available languages: %s",
                lang_code,
                self.get_available_languages(),
            )

        try:
            self.translator = gettext.translation(
                domain="messages",
                localedir=self.locales_dir,
                languages=[lang_code],
                fallback=True,
            )
            logger.info("Language set to %s", lang_code)

            self._ = self.translator.gettext
            self.language_changed.emit()
        except Exception as e:
            logger.error("Failed to set language '%s': %s", lang_code, e)

    def get_text(self, message: str) -> str:
        """Get translated text for a message"""
        if self._ is None:
            logger.warning("Translator not initialized, returning original message")
            return message
        return self._(message)  # pyright: ignore


language_manager = LanguageManager()


def _(message: str) -> str:
    return language_manager.get_text(message)
