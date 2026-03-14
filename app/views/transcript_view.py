from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from PySide6.QtCore import Slot
from PySide6.QtGui import (
    QColor,
    QPainter,
    QSyntaxHighlighter,
    QTextBlock,
    QTextCharFormat,
    QTextCursor,
    Qt,
)
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QScrollBar,
    QStyle,
    QStyleOptionSlider,
    QVBoxLayout,
    QWidget,
)

from app.constants import ThemeMode
from app.transcript import STTSegment
from app.view_model.transcript_vm import TranscriptViewModel

if TYPE_CHECKING:
    from app.theme_manager import ThemeManager


logger = logging.getLogger(__name__)

PROP_START = Qt.ItemDataRole.UserRole + 1
PROP_END = Qt.ItemDataRole.UserRole + 2


def block_get_times(block: QTextBlock) -> tuple[float, float]:
    it = block.begin()
    while not it.atEnd():
        fmt = it.fragment().charFormat()
        start = fmt.property(PROP_START)
        end = fmt.property(PROP_END)
        if start is not None:
            return float(start), float(end)
        it += 1
    return 0.0, 0.0


def block_set_times(cursor: QTextCursor, start: float, end: float) -> None:
    """Write timestamps into the block's char format via a tracked cursor edit."""
    fmt = QTextCharFormat()
    fmt.setProperty(PROP_START, start)
    fmt.setProperty(PROP_END, end)
    # Select the whole block content and merge the format — Qt records this
    # in its own undo stack automatically.
    cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
    cursor.mergeCharFormat(fmt)
    cursor.clearSelection()


class TranscriptTextEdit(QPlainTextEdit):
    @property
    def segments(self) -> list[STTSegment]:
        """Read current state directly from the document — O(n), cheap."""
        result = []
        block = self.document().begin()
        while block.isValid():
            start, end = block_get_times(block)
            result.append(
                STTSegment(
                    id=block.blockNumber(), start=start, end=end, text=block.text()
                )
            )
            block = block.next()
        return result

    def set_segment_start_time(self, block_number: int, start: float) -> None:
        print(f"set start time: {block_number}, start: {start}")
        """Edit start timestamp for one segment; the change joins the undo stack."""
        block = self.document().findBlockByNumber(block_number)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        fmt = QTextCharFormat()
        fmt.setProperty(PROP_START, start)
        # Select the whole block content and merge the format — Qt records this
        # in its own undo stack automatically.
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.mergeCharFormat(fmt)
        cursor.clearSelection()

    def set_segment_end_time(self, block_number: int, end: float) -> None:
        print(f"set end time: {block_number}, end: {end}")
        """Edit end timestamp for one segment; the change joins the undo stack."""
        block = self.document().findBlockByNumber(block_number)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        fmt = QTextCharFormat()
        fmt.setProperty(PROP_END, end)
        # Select the whole block content and merge the format — Qt records this
        # in its own undo stack automatically.
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.mergeCharFormat(fmt)
        cursor.clearSelection()

    def delete_segment(self, block_number: int) -> None:
        """Delete a segment's block; undoable."""
        block = self.document().findBlockByNumber(block_number)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        # If this wasn't the last block, also remove the trailing newline
        if block.next().isValid():
            cursor.deleteChar()

    def move_segment(self, block_number: int, direction: int) -> None:
        """Move segment up (-1) or down (+1); undoable as one edit block."""
        doc = self.document()
        block_a = doc.findBlockByNumber(block_number)
        block_b = doc.findBlockByNumber(block_number + direction)
        if not block_a.isValid() or not block_b.isValid():
            return

        text_a, text_b = block_a.text(), block_b.text()
        start_a, end_a = block_get_times(block_a)
        start_b, end_b = block_get_times(block_b)

        cursor = QTextCursor(doc)
        cursor.beginEditBlock()

        # Overwrite block_a with block_b's content
        c = QTextCursor(block_a)
        c.select(QTextCursor.SelectionType.BlockUnderCursor)
        c.removeSelectedText()
        c.insertText(text_b)
        block_set_times(c, start_b, end_b)

        # Overwrite block_b with block_a's content
        c = QTextCursor(doc.findBlockByNumber(block_number + direction))
        c.select(QTextCursor.SelectionType.BlockUnderCursor)
        c.removeSelectedText()
        c.insertText(text_a)
        block_set_times(c, start_a, end_a)

        cursor.endEditBlock()


class MarkerScrollBar(QScrollBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.markers: list[tuple[float, QColor]] = []

        self.current_marker_color = QColor("#4A90E2")
        self.hover_marker_color = QColor("#7FB3E8")

    def set_markers(
        self, current_index: int = -1, hover_index: int = -1, total_blocks: int = 1
    ) -> None:
        """Update current and hover markers."""
        markers = []
        if current_index >= 0:
            markers.append((current_index / total_blocks, self.current_marker_color))
        if hover_index >= 0:
            markers.append((hover_index / total_blocks, self.hover_marker_color))
        self.markers = markers
        self.update()

    def clear_hover(self, current_index: int = -1, total_blocks: int = 1) -> None:
        """Remove the hover marker but keep current marker if needed."""
        self.set_markers(
            current_index=current_index, hover_index=-1, total_blocks=total_blocks
        )

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.markers:
            return

        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)

        option = QStyleOptionSlider()
        self.initStyleOption(option)

        groove_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_ScrollBar,
            option,
            QStyle.SubControl.SC_ScrollBarGroove,
            self,
        )

        for ratio, color in self.markers:
            y = groove_rect.top() + ratio * groove_rect.height()
            painter.setBrush(color)

            painter.drawRect(
                groove_rect.left(),
                int(y),
                groove_rect.width(),
                3,
            )


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
        self.first_block = True

        current_theme = self.theme_manager.applied_theme
        self.set_highlight_colors(current_theme)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = TranscriptTextEdit()
        layout.addWidget(self.text_edit)

        self.highlighter = TranscriptHighlighter(
            document=self.text_edit.document(),
            color=self.highlight_color,
            hover_color=self.hover_color,
        )

        scrollbar = MarkerScrollBar(Qt.Orientation.Vertical)
        self.text_edit.setVerticalScrollBar(scrollbar)
        self.scrollbar = scrollbar

    def update_scroll_marker(self):
        block_count = self.text_edit.blockCount()
        self.scrollbar.set_markers(
            current_index=self.highlighter.current_block,
            hover_index=self.highlighter.hover_block,
            total_blocks=block_count,
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
        self.vm.segment_sent.connect(self._populate_transcript)
        self.vm.clear_requested.connect(self.text_edit.clear)
        self.vm.block_index_changed.connect(self.set_current_block)
        self.vm.hover_block_index_changed.connect(self.set_hover_block)
        self.vm.hover_block_reset.connect(self.reset_hover)
        # fmt: off
        self.vm.main_vm.start_segment_changed.connect(
            self.text_edit.set_segment_start_time
        )
        self.vm.main_vm.end_segment_changed.connect(
            self.text_edit.set_segment_end_time
        )
        # fmt: on
        self.theme_manager.theme_changed.connect(self.update_theme)
        self.vm.populate_segment_finished.connect(self._on_populate_segment_finished)
        self.text_edit.cursorPositionChanged.connect(self._on_cursor_position_changed)

    def _on_populate_segment_finished(self) -> None:
        self.first_block = True
        logger.debug(
            "Populate semgent finished: self.first_block restored to %s",
            self.first_block,
        )

    @Slot()
    def _on_cursor_position_changed(self) -> None:
        block = self.text_edit.textCursor().block()
        data = block_get_times(block)
        start = data[0]
        end = data[1]
        logger.debug(
            "Block: %s | Timestamps: [%f, %f]",
            block.blockNumber(),
            start,
            end,
        )
        self.vm.on_selected_segment_changed(
            id=block.blockNumber(), start=start, end=end
        )

    @Slot(int)
    def set_current_block(self, block_index: int) -> None:
        self.highlighter.set_current_block(block_index)
        self.update_scroll_marker()

    @Slot(int)
    def set_hover_block(self, block_index: int) -> None:
        self.highlighter.set_hover_block(block_index)
        self.update_scroll_marker()

    @Slot()
    def reset_hover(self) -> None:
        self.highlighter.reset_hover_block()
        block_count = self.text_edit.blockCount()
        self.scrollbar.clear_hover(
            current_index=self.highlighter.current_block, total_blocks=block_count
        )

    @Slot(STTSegment)
    def _populate_transcript(self, seg: STTSegment) -> None:
        self.text_edit.document().setUndoRedoEnabled(False)  # pause during bulk insert
        cursor = QTextCursor(self.text_edit.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.beginEditBlock()

        if not self.first_block:
            cursor.insertBlock()
        self.first_block = False

        cursor.insertText(seg.text)
        # Stamp timestamps onto the newly inserted text
        fmt = QTextCharFormat()
        fmt.setProperty(PROP_START, seg.start)
        fmt.setProperty(PROP_END, seg.end)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.mergeCharFormat(fmt)
        cursor.clearSelection()

        cursor.endEditBlock()
        self.text_edit.document().setUndoRedoEnabled(True)
        self.text_edit.document().clearUndoRedoStacks()
