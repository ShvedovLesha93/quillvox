from __future__ import annotations
from typing import TYPE_CHECKING, Dict
from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from app.constants import ThemeMode
from app.view_model.transcript_vm import TranscriptViewModel

if TYPE_CHECKING:
    from app.theme_manager import ThemeManager


class TranscriptHighlighter(QSyntaxHighlighter):
    """Highlights the current block/segment in the transcript."""

    def __init__(self, document, color: str, hover_color: str):
        super().__init__(document)
        self.current_block = -1
        self.hover_block = -1
        self.highlight_color = QColor(color)
        self.hover_color = QColor(hover_color)

    def set_current_block(self, block_index: int) -> None:
        """Update which block should be highlighted."""
        if self.current_block != block_index:
            self.current_block = block_index
            self.rehighlight()

    def set_hover_block(self, block_index: int) -> None:
        """Update which hover block should be highlighted."""
        if self.hover_block != block_index:
            self.hover_block = block_index
            self.rehighlight()

    def reset_hover_block(self) -> None:
        self.set_hover_block(-1)

    def highlightBlock(self, text: str) -> None:
        """Called automatically for each block during rendering."""
        block_num = self.currentBlock().blockNumber()
        fmt = QTextCharFormat()

        if block_num == self.current_block:
            fmt.setBackground(self.highlight_color)
            self.setFormat(0, len(text), fmt)
        elif block_num == self.hover_block:
            fmt.setBackground(self.hover_color)
            self.setFormat(0, len(text), fmt)

    def recolor(self, color: str, hover_color: str) -> None:
        """Change the highlight color and refresh if needed."""
        self.highlight_color = QColor(color)
        self.hover_color = QColor(hover_color)
        if self.current_block != -1:
            self.rehighlight()
        elif self.hover_block != -1:
            self.rehighlight()


class TranscriptView(QWidget):
    def __init__(
        self, transcript_vm: TranscriptViewModel, theme_manager: ThemeManager
    ) -> None:
        super().__init__()
        self.vm = transcript_vm
        self.theme_manager = theme_manager
        self.segment_positions = []

        self.highlight_color: str
        self.hover_color: str

        current_theme = self.theme_manager.applied_theme
        self.set_highlight_colors(current_theme)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QPlainTextEdit()
        layout.addWidget(self.text_edit)

        self.highlighter = TranscriptHighlighter(
            document=self.text_edit.document(),
            color=self.highlight_color,
            hover_color=self.hover_color,
        )

    def set_highlight_colors(self, theme: ThemeMode) -> None:
        if theme == ThemeMode.DARK:
            self.highlight_color = "#3C3C3C"
            self.hover_color = "#2A2A2A"
        else:
            self.highlight_color = "#E8E8E8"
            self.hover_color = "#D0D0D0"

    @Slot(object)
    def update_theme(self, theme: ThemeMode) -> None:
        self.set_highlight_colors(theme)
        self.highlighter.recolor(self.highlight_color, self.hover_color)

    def _connect_signals(self) -> None:
        self.vm.transcript_loaded.connect(self.text_edit.setPlainText)
        self.vm.segment_str.connect(self._populate_transcript)
        self.vm.clear_requested.connect(self.text_edit.clear)
        self.vm.block_index_changed.connect(self.highlighter.set_current_block)
        self.vm.hover_block_index_changed.connect(self.highlighter.set_hover_block)
        self.vm.hover_block_reset.connect(self.highlighter.reset_hover_block)
        self.theme_manager.theme_changed.connect(self.update_theme)

    @Slot(str)
    def _populate_transcript(self, text: str) -> None:
        """Load transcript segments into the text editor."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        cursor.insertText(text)
        cursor.insertBlock()
