from __future__ import annotations
from bisect import bisect_right
import logging
from typing import TYPE_CHECKING
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import (
    QColor,
    QKeySequence,
    QPainter,
    QSyntaxHighlighter,
    QTextBlock,
    QTextCharFormat,
    QTextCursor,
    Qt,
)
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QPushButton,
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
    from app.views.main_window import MainWindow
    from app.theme_manager import ThemeManager


logger = logging.getLogger(__name__)

PROP_START = Qt.ItemDataRole.UserRole + 1
PROP_END = Qt.ItemDataRole.UserRole + 2


class TranscriptTextEdit(QPlainTextEdit):
    first_block = True

    @property
    def segments(self) -> list[STTSegment]:
        """Read current state directly from the document — O(n), cheap."""
        result = []
        block = self.document().begin()
        while block.isValid():
            start, end = self.block_get_times(block)
            result.append(
                STTSegment(
                    id=block.blockNumber(), start=start, end=end, text=block.text()
                )
            )
            block = block.next()
        return result

    def set_segment_start_time(self, block_number: int, start: float) -> None:
        logging.info("set start time: block_number %s, start %s", block_number, start)
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
        logging.info("set end time: block_number %s, end %s", block_number, end)
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

    def append_segment(self, seg: STTSegment) -> None:
        self.document().setUndoRedoEnabled(False)  # pause during bulk insert
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.beginEditBlock()

        if not self.first_block:
            cursor.insertBlock()
        self.first_block = False

        cursor.insertText(seg.text.lstrip())
        # Stamp timestamps onto the newly inserted text
        fmt = QTextCharFormat()
        fmt.setProperty(PROP_START, seg.start)
        fmt.setProperty(PROP_END, seg.end)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.mergeCharFormat(fmt)
        cursor.clearSelection()

        cursor.endEditBlock()
        self.document().setUndoRedoEnabled(True)
        self.document().clearUndoRedoStacks()
        self.document().setModified(False)

    def block_get_times(self, block: QTextBlock) -> tuple[float, float]:
        it = block.begin()
        while not it.atEnd():
            fmt = it.fragment().charFormat()
            start = fmt.property(PROP_START)
            end = fmt.property(PROP_END)
            if start is not None:
                return float(start), float(end)
            it += 1
        return 0.0, 0.0


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
        self,
        main_window: MainWindow,
        transcript_vm: TranscriptViewModel,
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__()
        self.main_window = main_window
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
        self.text_edit.document().modificationChanged.connect(self._on_doc_changed)
        self.vm.current_position_changed.connect(self._on_position_changed)
        self.vm.hover_position_changed.connect(self._on_hover_position_changed)
        self.main_window.undo_pressed.connect(self._on_cursor_position_changed)
        self.main_window.redo_pressed.connect(self._on_cursor_position_changed)
        self.main_window.save_transcript_request.connect(self.save_transcript)

    @Slot(bool)
    def _on_doc_changed(self, state: bool) -> None:
        if self.main_window.is_process_alive:
            self.main_window.menu_bar.save.setEnabled(False)
            self.main_window.is_doc_changed = False
            self.main_window.on_modification_changed(False)
        else:
            self.main_window.menu_bar.save.setEnabled(state)
            self.main_window.is_doc_changed = state
            self.main_window.on_modification_changed(state)

    def _on_populate_segment_finished(self) -> None:
        self.text_edit.first_block = True
        logger.debug(
            "Populate semgent finished: self.first_block restored to %s",
            self.text_edit.first_block,
        )

    @Slot()
    def _on_cursor_position_changed(self) -> None:
        block = self.text_edit.textCursor().block()
        data = self.text_edit.block_get_times(block)
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
        self.text_edit.append_segment(seg)

    def find_block_at_position(self, position: float) -> int:
        """Find which block contains the given character position using binary search."""
        idx = bisect_right(self.text_edit.segments, position, key=lambda seg: seg.start)

        if idx == 0:
            return -1  # Position is before the first segment

        # Check if position falls within the previous segment
        seg = self.text_edit.segments[idx - 1]
        if seg.start <= position <= seg.end:
            return idx - 1

        return -1  # Position is in a gap between segments

    @Slot(float)
    def _on_position_changed(self, pos: float) -> None:
        idx = self.find_block_at_position(pos)
        self.set_current_block(idx)

    @Slot(int)
    def _on_hover_position_changed(self, pos: int) -> None:
        idx = self.find_block_at_position(pos)
        self.set_hover_block(idx)

    @Slot()
    def save_transcript(self) -> None:
        self.vm.save_transcript_requested.emit(self.text_edit.segments)
        self.text_edit.document().setModified(False)
