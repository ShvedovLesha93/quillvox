from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from app.view_model.transcript_vm import TranscriptViewModel


class TranscriptHighlighter(QSyntaxHighlighter):
    """Highlights the current block/segment in the transcript."""

    def __init__(self, document, color: str = "#3C3C3C", hover_color: str = "#2A2A2A"):
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

    def recolor(self, color: str) -> None:
        """Change the highlight color and refresh if needed."""
        self.highlight_color = QColor(color)
        if self.current_block != -1:
            self.rehighlight()


class TranscriptView(QWidget):
    def __init__(self, transcript_vm: TranscriptViewModel) -> None:
        super().__init__()
        self.vm = transcript_vm
        self.segment_positions = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QPlainTextEdit()
        layout.addWidget(self.text_edit)

        self.highlighter = TranscriptHighlighter(self.text_edit.document())

    def _connect_signals(self) -> None:
        self.vm.transcript_loaded.connect(self.text_edit.setPlainText)
        self.vm.segment_str.connect(self._populate_transcript)
        self.vm.clear_requested.connect(self.text_edit.clear)
        self.vm.block_index_changed.connect(self.highlighter.set_current_block)
        self.vm.hover_block_index_changed.connect(self.highlighter.set_hover_block)
        self.vm.hover_block_reset.connect(self.highlighter.reset_hover_block)

    @Slot(str)
    def _populate_transcript(self, text: str) -> None:
        """Load transcript segments into the text editor."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        cursor.insertText(text)
        cursor.insertBlock()
