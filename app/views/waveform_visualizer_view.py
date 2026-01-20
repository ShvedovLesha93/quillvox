import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout
import numpy as np


class WaveformVisualizer(QWidget):
    """High-performance waveform visualizer using PyQtGraph"""

    seek_started = Signal()
    position_moved = Signal(float)
    seek_finished = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data = None
        self.current_position = 0.0
        self.is_dragging = False

        self.setMinimumHeight(80)
        self.setMaximumHeight(120)

        self._setup_plot()

    def _setup_plot(self):
        """Initialize PyQtGraph plot widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

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

        # Remove padding
        self.plot_widget.setContentsMargins(0, 0, 0, 0)

        # Hide all buttons (auto-scale, etc.)
        self.plot_widget.hideButtons()

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

        # Create hover line (semi-transparent)
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

        layout.addWidget(self.plot_widget)

        # Connect mouse events
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_move)
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)

    def set_waveform_data(self, audio_data, sample_rate=None):
        """
        Set audio data for visualization with downsampling for performance

        Args:
            audio_data: numpy array of audio samples
            sample_rate: sample rate (optional)
        """
        if audio_data is None:
            self.waveform_data = None
            self.waveform_played.setData([])
            self.waveform_unplayed.setData([])
            return

        # Convert to numpy array if needed
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data)

        # Handle stereo by converting to mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Normalize to -1.0 to 1.0 range
        if audio_data.max() > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        # Downsample for performance (keep ~2000-4000 points for smooth visualization)
        target_points = 3000
        if len(audio_data) > target_points:
            # Downsample by taking min/max in chunks for accurate waveform
            chunk_size = len(audio_data) // (target_points // 2)
            downsampled = []
            x_vals = []

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i : i + chunk_size]
                if len(chunk) > 0:
                    downsampled.extend([np.min(chunk), np.max(chunk)])
                    x_vals.extend([i, i + len(chunk) - 1])

            self.waveform_data = np.array(downsampled)
            self.x_data = np.array(x_vals)
        else:
            self.waveform_data = audio_data
            self.x_data = np.arange(len(audio_data))

        # Set Y-axis range
        self.plot_widget.setYRange(-1.1, 1.1, padding=0)

        # Update waveform display
        self._update_waveform_display()

    def _update_waveform_display(self):
        """Update the waveform plots based on current position"""
        if self.waveform_data is None or len(self.waveform_data) == 0:
            return

        # Calculate split point based on position
        total_samples = len(self.x_data)
        split_index = int(self.current_position * total_samples)
        split_index = max(0, min(split_index, total_samples))

        # Update X-axis range
        if len(self.x_data) > 0:
            self.plot_widget.setXRange(self.x_data[0], self.x_data[-1], padding=0)

            # Update position line
            pos_x = self.x_data[0] + self.current_position * (
                self.x_data[-1] - self.x_data[0]
            )
            self.position_line.setPos(pos_x)

        # Split waveform into played and unplayed
        if split_index > 0:
            self.waveform_played.setData(
                self.x_data[:split_index], self.waveform_data[:split_index]
            )
        else:
            self.waveform_played.setData([])

        if split_index < total_samples:
            self.waveform_unplayed.setData(
                self.x_data[split_index:], self.waveform_data[split_index:]
            )
        else:
            self.waveform_unplayed.setData([])

    def set_position(self, position):
        """Set current playback position (0.0 to 1.0)"""
        self.current_position = max(0.0, min(1.0, position))
        if not self.is_dragging:
            self._update_waveform_display()

    def _get_position_from_scene(self, scene_pos):
        """Convert scene position to normalized position (0.0 to 1.0)"""
        if self.waveform_data is None or len(self.x_data) == 0:
            return 0.0

        view_box = self.plot_widget.getViewBox()
        mouse_point = view_box.mapSceneToView(scene_pos)
        x = mouse_point.x()

        # Normalize to 0.0 - 1.0
        x_min, x_max = self.x_data[0], self.x_data[-1]
        position = (x - x_min) / (x_max - x_min) if x_max > x_min else 0.0
        return max(0.0, min(1.0, position))

    def _on_mouse_move(self, pos):
        """Handle mouse movement for hover and drag"""
        if self.waveform_data is None:
            return

        position = self._get_position_from_scene(pos)

        if self.is_dragging:
            # Update position while dragging
            self.current_position = position
            self._update_waveform_display()
            self.position_moved.emit(position)
        else:
            # Show hover line
            if len(self.x_data) > 0:
                x_min, x_max = self.x_data[0], self.x_data[-1]
                hover_x = x_min + position * (x_max - x_min)
                self.hover_line.setPos(hover_x)
                self.hover_line.setVisible(True)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _on_mouse_click(self, event):
        """Handle mouse clicks for seeking"""
        if self.waveform_data is None:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            position = self._get_position_from_scene(event.scenePos())

            if event.double():
                # Double click - just seek
                self.current_position = position
                self._update_waveform_display()
                self.seek_started.emit()
                self.position_moved.emit(position)
                self.seek_finished.emit(position)
            else:
                # Single click - start drag
                self.is_dragging = True
                self.current_position = position
                self._update_waveform_display()
                self.seek_started.emit()
                self.position_moved.emit(position)
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finish seeking"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.seek_finished.emit(self.current_position)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def leaveEvent(self, event):
        """Hide hover line when mouse leaves"""
        self.hover_line.setVisible(False)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

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
