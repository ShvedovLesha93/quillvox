from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.constants import ThemeMode
from app.theme_manager import ThemeManager
from app.utils.time_format import format_time

if TYPE_CHECKING:
    from numpy import ndarray
    from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent
    from PySide6.QtCore import QPointF

    from app.view_model.waveform_vm import WaveformViewModel

import logging

logger = logging.getLogger(__name__)


class WaveformView(QWidget):
    """High-performance waveform visualizer using PyQtGraph's built-in optimizations"""

    position_changed = Signal(int)
    loading_finished = Signal()
    hover_position_changed = Signal(int)
    hover_left = Signal()

    def __init__(
        self, waveform_vm: WaveformViewModel, theme_manager: ThemeManager, parent=None
    ) -> None:
        super().__init__(parent)
        self.vm = waveform_vm
        self.theme_manager = theme_manager

        self.x_data = None
        self.original_length = 0
        self.current_position = 0.0
        self.duration: int

        self.current_segment_id = 0
        self._drag_mode: Literal[
            "idle", "dragging_start", "dragging_end", "dragging_new", "seeking"
        ] = "idle"
        self._drag_new_anchor: float = (
            0.0  # anchor sample position when drawing a new selection
        )
        HANDLE_GRAB_THRESHOLD_PX = 10  # pixels within which we grab a handle

        self._setup_ui()
        self.update_theme(self.theme_manager.applied_theme)
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Time label for hover position
        self.position_label = QLabel()
        self.position_label.setObjectName("timelineLabel")
        self.position_label.setVisible(False)
        self.position_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )  # Don't block mouse events

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMouseTracking(True)

        self.position_label.setParent(self.plot_widget)
        self.position_label.raise_()

        # Configure axes
        self.plot_widget.showGrid(x=False, y=False)
        self.plot_widget.hideAxis("left")
        self.plot_widget.hideAxis("bottom")
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.plot_widget.setContentsMargins(0, 0, 0, 0)

        # Get ViewBox for custom zoom behavior
        self.view_box = self.plot_widget.getViewBox()
        self.view_box.setMouseEnabled(
            x=True, y=False
        )  # Allow horizontal panning/zooming
        self.view_box.setLimits(yMin=-1.2, yMax=1.2)  # Limit Y axis

        # Single waveform plot
        self.waveform = self.plot_widget.plot(
            pen=pg.mkPen(color=(100, 180, 255), width=1)
        )

        self.waveform.setDownsampling(auto=True)
        self.waveform.setClipToView(True)

        # Position line
        self.position_line = pg.InfiniteLine(
            pos=0, angle=90, pen=pg.mkPen(color=(255, 100, 100), width=2), movable=False
        )
        self.position_line.setVisible(False)
        self.plot_widget.addItem(self.position_line)

        # Hover line
        self.hover_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color=(255, 100, 100, 100), width=2),
            movable=False,
        )
        self.hover_line.setVisible(False)
        self.plot_widget.addItem(self.hover_line)

        # Selection region
        self.selection_region = pg.LinearRegionItem(
            values=(0, 0),
            brush=pg.mkBrush(100, 180, 255, 50),
            pen=pg.mkPen(color=(100, 180, 255), width=1),
            movable=False,
        )
        self.selection_region.setVisible(False)
        self.plot_widget.addItem(self.selection_region)

        # X-axis line
        self.x_axis_line = pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen(color=(80, 80, 80), width=1), movable=False
        )
        self.plot_widget.addItem(self.x_axis_line)

        layout.addWidget(self.plot_widget)

        # Mouse events
        self.plot_widget.viewport().installEventFilter(self)

    def _connect_signals(self) -> None:
        self.theme_manager.theme_changed.connect(self.update_theme)
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_move)  # type: ignore
        # self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)  # type: ignore
        self.vm.changed_selected_segment.connect(self.set_selection)
        self.plot_widget.viewport().installEventFilter(self)

    @Slot(object)
    def update_theme(self, theme: ThemeMode) -> None:
        if theme == ThemeMode.DARK:
            self.plot_widget.setBackground((25, 25, 25))
            self.plot_widget.setStyleSheet("")
            self.waveform.setPen(pg.mkPen(color=(100, 180, 255), width=1))

            # Update other lines too
            self.position_line.setPen(pg.mkPen(color=(255, 100, 100), width=2))
            self.hover_line.setPen(pg.mkPen(color=(255, 100, 100, 100), width=2))
            self.x_axis_line.setPen(pg.mkPen(color=(80, 80, 80), width=1))
            self.selection_region.setBrush(pg.mkBrush(100, 180, 255, 50))
            self.selection_region.setBrush(pg.mkBrush(100, 180, 255, 50))
            for line in self.selection_region.lines:
                line.setPen(pg.mkPen(color=(100, 180, 255, 180), width=1))
        else:
            self.plot_widget.setBackground((255, 255, 255))
            self.plot_widget.setStyleSheet("border: 1px solid rgb(195, 195, 195);")
            self.waveform.setPen(pg.mkPen(color=(45, 45, 45), width=1))

            # Update other lines for light theme
            self.position_line.setPen(pg.mkPen(color=(255, 0, 0), width=2))
            self.hover_line.setPen(pg.mkPen(color=(255, 0, 0, 100), width=2))
            self.x_axis_line.setPen(pg.mkPen(color=(200, 200, 200), width=1))
            self.selection_region.setBrush(pg.mkBrush(45, 45, 45, 50))
            self.selection_region.setBrush(pg.mkBrush(45, 120, 220, 40))
            for line in self.selection_region.lines:
                line.setPen(pg.mkPen(color=(45, 120, 220, 160), width=1))

    def reset(self) -> None:
        """Reset the visualizer to empty state"""
        self.x_data = None
        self.original_length = 0
        self.current_position = 0.0
        self.waveform.setData([])
        self.position_line.setPos(0)
        self.position_line.setEnabled(False)
        self.clear_selection()

    def set_position(self, position: float) -> None:
        """Set current playback position (0.0 to 1.0)"""
        new_value = position / self.duration
        self.current_position = max(0.0, min(1.0, new_value))
        pos_sample = int(self.current_position * self.original_length)
        self.position_line.setPos(pos_sample)

    def load_waveform(self, x_data: ndarray, waveform_data: ndarray) -> None:
        """Callback when waveform data is loaded"""
        self.x_data = x_data
        self.original_length = x_data[-1] if len(x_data) > 0 else len(waveform_data)

        # Set initial view range
        self.view_box.setLimits(xMin=0, xMax=self.original_length)
        self.view_box.setRange(
            xRange=(0, self.original_length), yRange=(-1.1, 1.1), padding=0
        )

        # Update display
        self.position_line.setVisible(True)
        self.waveform.setData(x_data, waveform_data)

        # Emit signal that loading is finished
        self.loading_finished.emit()

    @Slot(int, float, float)
    def set_selection(self, segment_id: int, start: float, end: float) -> None:
        """
        Display a selection region between start and end (milliseconds).

        Args:
            segment_id: ID of the segment being selected
            start: Selection start in milliseconds
            end: Selection end in milliseconds
        """
        if self.original_length == 0 or self.duration == 0:
            logger.warning("set_selection called before waveform loaded, skipping")
            return

        self.current_segment_id = segment_id

        start_sample = int((start / self.duration) * self.original_length) * 1000
        end_sample = int((end / self.duration) * self.original_length) * 1000

        logger.debug(
            "set_selection: segment_id=%d start=%.3f ms -> sample=%d | end=%.3f ms -> sample=%d",
            segment_id,
            start,
            start_sample,
            end,
            end_sample,
        )

        self.selection_region.setRegion((start_sample, end_sample))
        self.selection_region.setVisible(True)

    def clear_selection(self) -> None:
        """Hide and reset the selection region"""
        self.selection_region.setVisible(False)
        self.selection_region.setRegion((0, 0))

    def _get_position_from_scene(self, scene_pos: QPointF) -> float:
        """Convert scene position to normalized position (0.0 to 1.0)"""
        if self.original_length == 0:
            return 0.0

        mouse_point = self.view_box.mapSceneToView(scene_pos)
        x = mouse_point.x()

        # x is in original sample coordinates
        position = x / self.original_length if self.original_length > 0 else 0.0
        result = max(0.0, min(1.0, position))
        return result

    def _on_mouse_move(self, pos: QPointF) -> None:
        """Handle mouse movement: hover display and selection dragging."""
        if self.x_data is None:
            return

        position = self._get_position_from_scene(pos)
        hover_x = position * self.original_length
        hover_pos_sample = int(position * self.duration)

        # --- Drag in progress ---
        if self._drag_mode == "dragging_start":
            start_sample = hover_x
            _, end_sample = self.selection_region.getRegion()
            self.selection_region.setRegion((start_sample, end_sample))
            self._emit_selection_changed()
            logger.debug("Dragging start handle to sample=%.1f", start_sample)

        elif self._drag_mode == "dragging_end":
            start_sample, _ = self.selection_region.getRegion()
            self.selection_region.setRegion((start_sample, hover_x))
            self._emit_selection_changed()
            logger.debug("Dragging end handle to sample=%.1f", hover_x)

        # --- Cursor shape based on proximity to handles ---
        else:
            near = self._is_near_handle(pos)
            if near in ("start", "end"):
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # --- Hover label and line (always updated) ---
        self.position_label.setText(format_time(hover_pos_sample, show_ms=True))
        self.position_label.adjustSize()

        widget_pos = self.plot_widget.mapFromScene(pos)
        widget_width = self.plot_widget.width()
        label_width = self.position_label.width()

        x_offset = (
            -(label_width + 15)
            if widget_pos.x() + 15 + label_width > widget_width
            else 15
        )
        y_offset = 15 if widget_pos.y() - 25 < 0 else -25

        self.position_label.move(widget_pos.x() + x_offset, widget_pos.y() + y_offset)
        self.position_label.setVisible(True)

        self.hover_line.setPos(hover_x)
        self.hover_line.setVisible(True)
        self.hover_position_changed.emit(hover_pos_sample)

    def _on_mouse_click(self, event: MouseClickEvent) -> None:
        """Handle mouse clicks for seeking"""
        if self.x_data is None:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            position = self._get_position_from_scene(event.scenePos())

            self.current_position = position
            pos_sample = int(position * self.original_length)
            self.position_line.setPos(pos_sample)
            current_pos_sample = int(self.current_position * self.duration)
            self.position_changed.emit(current_pos_sample)

    def leaveEvent(self, event) -> None:
        """Hide hover line when mouse leaves"""
        self.hover_line.setVisible(False)
        self.hover_left.emit()
        self.position_label.setVisible(False)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def _sample_to_scene_x(self, sample: float) -> float:
        """Convert a sample position to scene X coordinate."""
        scene_pos = self.view_box.mapViewToScene(pg.Point(sample, 0))
        return scene_pos.x()

    def _is_near_handle(self, scene_pos: QPointF, threshold_px: int = 10) -> str:
        """
        Return which selection handle the cursor is near.
        Returns 'start', 'end', or 'none'.
        """
        if not self.selection_region.isVisible():
            return "none"

        start_sample, end_sample = self.selection_region.getRegion()

        start_scene_x = self._sample_to_scene_x(start_sample)
        end_scene_x = self._sample_to_scene_x(end_sample)
        cursor_x = scene_pos.x()

        if abs(cursor_x - start_scene_x) <= threshold_px:
            return "start"
        if abs(cursor_x - end_scene_x) <= threshold_px:
            return "end"
        return "none"

    def _emit_selection_changed(self) -> None:
        """Read current region and emit both boundary signals in milliseconds."""
        start_sample, end_sample = self.selection_region.getRegion()  # pyright: ignore

        # Clamp to valid range
        start_sample = max(0.0, min(float(self.original_length), start_sample))
        end_sample = max(0.0, min(float(self.original_length), end_sample))

        # Ensure start <= end
        if start_sample > end_sample:
            start_sample, end_sample = end_sample, start_sample

        start_sec = ((start_sample / self.original_length) * self.duration) / 1000
        end_sec = ((end_sample / self.original_length) * self.duration) / 1000

        self.vm.start_selection_changed.emit(self.current_segment_id, start_sec)
        self.vm.end_selection_changed.emit(self.current_segment_id, end_sec)

    def _on_mouse_press(self, event) -> None:
        """Determine drag mode on mouse button press."""
        if self.x_data is None:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return

        scene_pos = self.plot_widget.mapToScene(event.pos())
        near = self._is_near_handle(scene_pos)

        if near == "start":
            self.view_box.setMouseEnabled(x=False, y=False)
            self._drag_mode = "dragging_start"
            logger.debug("Started dragging start handle")
        elif near == "end":
            self.view_box.setMouseEnabled(x=False, y=False)
            self._drag_mode = "dragging_end"
            logger.debug("Started dragging end handle")
        else:
            logger.debug("Press outside handles — will seek on release")
            self._drag_mode = "seeking"

    def _on_mouse_release(self, event) -> None:
        """Finalize handle drag or seek on mouse button release."""
        self.view_box.setMouseEnabled(x=True, y=False)
        if self.x_data is None:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return

        scene_pos = self.plot_widget.mapToScene(event.pos())
        position = self._get_position_from_scene(scene_pos)

        if self._drag_mode in ("dragging_start", "dragging_end"):
            self._emit_selection_changed()
            logger.debug("Handle drag committed, mode=%s", self._drag_mode)

        elif self._drag_mode == "seeking":
            self._seek(position)

        self._drag_mode = "idle"

    def _seek(self, position: float) -> None:
        """Seek playback to a normalized position (0.0–1.0)."""
        self.current_position = position
        pos_sample = int(position * self.original_length)
        self.position_line.setPos(pos_sample)
        current_pos_ms = int(self.current_position * self.duration)
        logger.debug("Seek to position=%.4f -> %d ms", position, current_pos_ms)
        self.position_changed.emit(current_pos_ms)

    def eventFilter(self, obj, event) -> bool:
        from PySide6.QtCore import QEvent

        if obj is self.plot_widget.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                self._on_mouse_press(event)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._on_mouse_release(event)
        return super().eventFilter(obj, event)
