from __future__ import annotations
from typing import TYPE_CHECKING
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout

from app.constants import ThemeMode
from app.theme_manager import ThemeManager


if TYPE_CHECKING:
    from numpy import ndarray
    from app.view_model.waveform_vm import WaveformViewModel
    from PySide6.QtCore import QPointF
    from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent

import logging

logger = logging.getLogger(__name__)


class WaveformView(QWidget):
    """High-performance waveform visualizer using PyQtGraph's built-in optimizations"""

    seek_started = Signal()
    position_moved = Signal(float)
    seek_finished = Signal(float)
    loading_finished = Signal()
    loading_error = Signal(str)

    def __init__(
        self, waveform_vm: WaveformViewModel, theme_manager: ThemeManager, parent=None
    ) -> None:
        super().__init__(parent)
        self.vm = waveform_vm
        self.theme_manager = theme_manager

        self.x_data = None
        self.original_length = 0
        self.current_position = 0.0
        self.is_dragging = False

        self.setMinimumHeight(80)
        self.setMaximumHeight(120)

        self._setup_ui()
        self.update_theme(self.theme_manager.applied_theme)
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMouseTracking(True)

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
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)  # type: ignore

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
        else:
            self.plot_widget.setBackground((255, 255, 255))
            self.plot_widget.setStyleSheet("border: 1px solid rgb(195, 195, 195);")
            self.waveform.setPen(pg.mkPen(color=(45, 45, 45), width=1))

            # Update other lines for light theme
            self.position_line.setPen(pg.mkPen(color=(255, 0, 0), width=2))
            self.hover_line.setPen(pg.mkPen(color=(255, 0, 0, 100), width=2))
            self.x_axis_line.setPen(pg.mkPen(color=(200, 200, 200), width=1))

    def reset(self) -> None:
        """Reset the visualizer to empty state"""
        self.x_data = None
        self.original_length = 0
        self.current_position = 0.0
        self.waveform.setData([])
        self.position_line.setPos(0)
        self.position_line.setEnabled(False)

    def set_position(self, position: float) -> None:
        """Set current playback position (0.0 to 1.0)"""
        self.current_position = max(0.0, min(1.0, position))

        if not self.is_dragging and self.original_length > 0:
            # Just update position line - waveform stays stable
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
        """Handle mouse movement for hover and drag"""
        if self.x_data is None:
            return

        position = self._get_position_from_scene(pos)

        if self.is_dragging:
            self.current_position = position
            pos_sample = int(position * self.original_length)
            self.position_line.setPos(pos_sample)
            self.position_moved.emit(position)
        else:
            # Show hover line
            hover_x = position * self.original_length
            self.hover_line.setPos(hover_x)
            self.hover_line.setVisible(True)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _on_mouse_click(self, event: MouseClickEvent) -> None:
        """Handle mouse clicks for seeking"""
        if self.x_data is None:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            position = self._get_position_from_scene(event.scenePos())

            self.is_dragging = True
            self.current_position = position
            pos_sample = int(position * self.original_length)
            self.position_line.setPos(pos_sample)
            self.seek_started.emit()
            self.position_moved.emit(position)
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release to finish seeking"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.seek_finished.emit(self.current_position)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def leaveEvent(self, event) -> None:
        """Hide hover line when mouse leaves"""
        self.hover_line.setVisible(False)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
