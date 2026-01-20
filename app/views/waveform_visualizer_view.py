import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollBar
import numpy as np


class WaveformVisualizer(QWidget):
    """High-performance waveform visualizer using PyQtGraph"""

    seek_started = Signal()
    position_moved = Signal(float)
    seek_finished = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data = None
        self.x_data = None
        self.current_position = 0.0
        self.is_dragging = False
        self.zoom_level = 1.0
        self.view_center = 0.5  # Center of visible area (0.0 to 1.0)

        # Cache for performance
        self._cached_visible_range = None
        self._cached_display_data = None
        self._last_split_sample = -1

        self.setMinimumHeight(80)
        self.setMaximumHeight(120)

        self._setup_plot()

    def _setup_plot(self):
        """Initialize PyQtGraph plot widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground((40, 40, 40))
        self.plot_widget.setMouseTracking(True)

        # Configure axes
        self.plot_widget.showGrid(x=False, y=False)
        self.plot_widget.hideAxis("left")
        self.plot_widget.hideAxis("bottom")
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.plot_widget.setContentsMargins(0, 0, 0, 0)

        # Create plot items
        self.waveform_played = self.plot_widget.plot(
            pen=pg.mkPen(color=(60, 120, 180), width=1)
        )
        self.waveform_unplayed = self.plot_widget.plot(
            pen=pg.mkPen(color=(100, 180, 255), width=1)
        )

        # Create position line
        self.position_line = pg.InfiniteLine(
            pos=0, angle=90, pen=pg.mkPen(color=(255, 100, 100), width=2), movable=False
        )
        self.plot_widget.addItem(self.position_line)

        # Create hover line
        self.hover_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color=(255, 100, 100, 100), width=2),
            movable=False,
        )
        self.hover_line.setVisible(False)
        self.plot_widget.addItem(self.hover_line)

        # Add center line
        self.center_line = pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen(color=(80, 80, 80), width=1), movable=False
        )
        self.plot_widget.addItem(self.center_line)

        # Create horizontal scrollbar
        scrollbar_layout = QHBoxLayout()
        scrollbar_layout.setContentsMargins(0, 0, 0, 0)

        self.h_scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        self.h_scrollbar.setRange(0, 1000)
        self.h_scrollbar.setValue(500)
        self.h_scrollbar.setVisible(False)
        self.h_scrollbar.valueChanged.connect(self._on_scroll)

        scrollbar_layout.addWidget(self.h_scrollbar)

        layout.addWidget(self.plot_widget)
        layout.addLayout(scrollbar_layout)

        # Connect mouse events
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_move)
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)
        self.plot_widget.viewport().installEventFilter(self)

    def set_waveform_data(self, audio_data, sample_rate=None):
        """Set audio data for visualization - keeps full resolution"""
        if audio_data is None:
            self.waveform_data = None
            self.x_data = None
            self.waveform_played.setData([])
            self.waveform_unplayed.setData([])
            self._cached_visible_range = None
            self._cached_display_data = None
            self._last_split_sample = -1
            return

        # Convert to numpy array
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data)

        # Handle stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Normalize
        if audio_data.max() > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        # Store full resolution data
        self.waveform_data = audio_data
        self.x_data = np.arange(len(audio_data))

        # Reset zoom and cache
        self.zoom_level = 1.0
        self.view_center = 0.5
        self._cached_visible_range = None
        self._cached_display_data = None
        self._last_split_sample = -1

        # Set Y-axis range
        self.plot_widget.setYRange(-1.1, 1.1, padding=0)

        # Update display
        self._update_waveform_display(force_redraw=True)

    def _get_visible_range(self):
        """Calculate the visible sample range based on zoom and center"""
        if self.waveform_data is None:
            return 0, 0

        total_samples = len(self.x_data)
        visible_fraction = 1.0 / self.zoom_level
        visible_samples = int(total_samples * visible_fraction)

        # Calculate start based on center position
        center_sample = int(self.view_center * total_samples)
        start_idx = int(center_sample - visible_samples / 2)

        # Clamp to valid range
        start_idx = max(0, min(start_idx, total_samples - visible_samples))
        end_idx = min(start_idx + visible_samples, total_samples)

        return start_idx, end_idx

    def _downsample_for_display(self, x_data, y_data, target_points=10000):
        """Downsample data intelligently for display performance"""
        if len(x_data) <= target_points:
            return x_data, y_data

        # Calculate chunk size
        chunk_size = len(x_data) // (target_points // 2)

        downsampled_x = []
        downsampled_y = []

        for i in range(0, len(x_data), chunk_size):
            chunk_x = x_data[i : i + chunk_size]
            chunk_y = y_data[i : i + chunk_size]

            if len(chunk_y) > 0:
                # Keep min and max for accurate waveform representation
                min_idx = np.argmin(chunk_y)
                max_idx = np.argmax(chunk_y)

                if min_idx < max_idx:
                    downsampled_x.extend([chunk_x[min_idx], chunk_x[max_idx]])
                    downsampled_y.extend([chunk_y[min_idx], chunk_y[max_idx]])
                else:
                    downsampled_x.extend([chunk_x[max_idx], chunk_x[min_idx]])
                    downsampled_y.extend([chunk_y[max_idx], chunk_y[min_idx]])

        return np.array(downsampled_x), np.array(downsampled_y)

    def _update_waveform_display(self, force_redraw=False):
        """Update the waveform display based on zoom and position"""
        if self.waveform_data is None or len(self.waveform_data) == 0:
            return

        # Get visible range
        start_idx, end_idx = self._get_visible_range()

        # Check if we need to redraw the waveform data
        need_redraw = force_redraw or self._cached_visible_range != (start_idx, end_idx)

        # Update scrollbar visibility and value
        if self.zoom_level > 1.0:
            self.h_scrollbar.setVisible(True)
            self.h_scrollbar.blockSignals(True)
            self.h_scrollbar.setValue(int(self.view_center * 1000))
            self.h_scrollbar.setPageStep(int(1000 / self.zoom_level))
            self.h_scrollbar.blockSignals(False)
        else:
            self.h_scrollbar.setVisible(False)

        if need_redraw:
            # Get visible data
            visible_x = self.x_data[start_idx:end_idx]
            visible_y = self.waveform_data[start_idx:end_idx]

            if len(visible_x) == 0:
                return

            # Downsample for performance if needed
            display_x, display_y = self._downsample_for_display(visible_x, visible_y)

            # Cache the display data
            self._cached_visible_range = (start_idx, end_idx)
            self._cached_display_data = (display_x, display_y)

            # Update plot range
            self.plot_widget.setXRange(visible_x[0], visible_x[-1], padding=0)

        # Use cached data if available
        if self._cached_display_data is None:
            return

        display_x, display_y = self._cached_display_data

        # Calculate position sample
        total_samples = len(self.x_data)
        pos_sample = int(self.current_position * total_samples)

        # Only update position line (very fast)
        self.position_line.setPos(pos_sample)

        # Only update split if position changed significantly (optimization)
        if need_redraw or abs(pos_sample - self._last_split_sample) > max(
            1, total_samples // 1000
        ):
            self._last_split_sample = pos_sample

            # Split into played/unplayed
            split_mask = display_x <= pos_sample

            if np.any(split_mask):
                self.waveform_played.setData(
                    display_x[split_mask], display_y[split_mask]
                )
            else:
                self.waveform_played.setData([])

            if np.any(~split_mask):
                self.waveform_unplayed.setData(
                    display_x[~split_mask], display_y[~split_mask]
                )
            else:
                self.waveform_unplayed.setData([])

    def set_position(self, position):
        """Set current playback position (0.0 to 1.0) - optimized for playback"""
        self.current_position = max(0.0, min(1.0, position))
        if not self.is_dragging:
            # During playback, only update position line, not entire waveform
            if self.waveform_data is not None and len(self.x_data) > 0:
                total_samples = len(self.x_data)
                pos_sample = int(self.current_position * total_samples)
                self.position_line.setPos(pos_sample)

                # Only update split every ~0.1% to reduce CPU usage
                if abs(pos_sample - self._last_split_sample) > max(
                    1, total_samples // 1000
                ):
                    self._update_waveform_display(force_redraw=False)

    def _get_position_from_scene(self, scene_pos):
        """Convert scene position to normalized position"""
        if self.waveform_data is None or len(self.x_data) == 0:
            return 0.0

        view_box = self.plot_widget.getViewBox()
        mouse_point = view_box.mapSceneToView(scene_pos)
        x = mouse_point.x()

        # Convert to normalized position
        total_samples = len(self.x_data)
        position = x / total_samples if total_samples > 0 else 0.0
        return max(0.0, min(1.0, position))

    def _on_mouse_move(self, pos):
        """Handle mouse movement"""
        if self.waveform_data is None:
            return

        position = self._get_position_from_scene(pos)

        if self.is_dragging:
            self.current_position = position
            self._update_waveform_display(force_redraw=False)
            self.position_moved.emit(position)
        else:
            # Show hover line
            total_samples = len(self.x_data)
            hover_x = position * total_samples
            self.hover_line.setPos(hover_x)
            self.hover_line.setVisible(True)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _on_mouse_click(self, event):
        """Handle mouse clicks"""
        if self.waveform_data is None:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            position = self._get_position_from_scene(event.scenePos())

            self.is_dragging = True
            self.current_position = position
            self._update_waveform_display(force_redraw=False)
            self.seek_started.emit()
            self.position_moved.emit(position)
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.seek_finished.emit(self.current_position)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def leaveEvent(self, event):
        """Hide hover line when mouse leaves"""
        self.hover_line.setVisible(False)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def eventFilter(self, obj, event):
        """Handle wheel events for zooming"""
        if event.type() == event.Type.Wheel and obj == self.plot_widget.viewport():
            if self.waveform_data is not None and len(self.waveform_data) > 0:
                delta = event.angleDelta().y()
                zoom_factor = 1.2 if delta > 0 else 1 / 1.2

                # Get mouse position in normalized coordinates (0.0 to 1.0)
                view_box = self.plot_widget.getViewBox()
                scene_pos = self.plot_widget.mapToScene(event.position().toPoint())
                mouse_point = view_box.mapSceneToView(scene_pos)

                total_samples = len(self.x_data)
                mouse_norm = (
                    mouse_point.x() / total_samples if total_samples > 0 else 0.5
                )
                mouse_norm = max(0.0, min(1.0, mouse_norm))

                # Apply zoom
                old_zoom = self.zoom_level
                self.zoom_level *= zoom_factor
                self.zoom_level = max(1.0, min(100.0, self.zoom_level))

                if old_zoom != self.zoom_level:
                    # Adjust view center to keep mouse position stable
                    old_visible_fraction = 1.0 / old_zoom
                    new_visible_fraction = 1.0 / self.zoom_level

                    # Calculate where mouse was in the old view
                    old_view_start = self.view_center - old_visible_fraction / 2
                    mouse_in_view = (mouse_norm - old_view_start) / old_visible_fraction

                    # Keep mouse at same relative position in new view
                    new_view_start = mouse_norm - mouse_in_view * new_visible_fraction
                    self.view_center = new_view_start + new_visible_fraction / 2

                    # Clamp view center
                    half_visible = new_visible_fraction / 2
                    self.view_center = max(
                        half_visible, min(1.0 - half_visible, self.view_center)
                    )

                    self._update_waveform_display(force_redraw=True)

                return True

        return super().eventFilter(obj, event)

    def _on_scroll(self, value):
        """Handle scrollbar movement"""
        if self.waveform_data is not None and self.zoom_level > 1.0:
            self.view_center = value / 1000.0

            # Clamp to valid range
            visible_fraction = 1.0 / self.zoom_level
            half_visible = visible_fraction / 2
            self.view_center = max(
                half_visible, min(1.0 - half_visible, self.view_center)
            )

            self._update_waveform_display(force_redraw=True)

    def generate_sample_waveform(self, duration_seconds=10, sample_rate=44100):
        """Generate a sample waveform for testing"""
        t = np.linspace(0, duration_seconds, int(duration_seconds * sample_rate))
        waveform = (
            np.sin(2 * np.pi * 440 * t) * 0.5
            + np.sin(2 * np.pi * 880 * t) * 0.3
            + np.sin(2 * np.pi * 220 * t) * 0.2
        )
        envelope = np.exp(-t / duration_seconds * 2)
        waveform = waveform * envelope
        self.set_waveform_data(waveform, sample_rate)
