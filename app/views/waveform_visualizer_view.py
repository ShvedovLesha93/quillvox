from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QCursor
import numpy as np


class WaveformVisualizer(QWidget):
    """Widget for visualizing audio waveform with current position indicator"""

    position_clicked = Signal(float)  # Emits normalized position (0.0 to 1.0)
    position_moved = Signal(float)  # Emits normalized position while dragging
    seek_started = Signal()  # Emitted when user starts dragging
    seek_finished = Signal(float)  # Emitted when user finishes dragging

    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data = None
        self.current_position = 0.0  # Position from 0.0 to 1.0
        self.is_dragging = False
        self.hover_position = None

        self.setMinimumHeight(80)
        self.setMaximumHeight(120)
        self.setMouseTracking(True)  # Enable hover detection

        # Colors
        self.bg_color = QColor(40, 40, 40)
        self.waveform_color = QColor(100, 180, 255)
        self.waveform_played_color = QColor(60, 120, 180)
        self.position_line_color = QColor(255, 100, 100)
        self.hover_line_color = QColor(255, 100, 100, 100)  # Semi-transparent
        self.center_line_color = QColor(80, 80, 80)

    def set_waveform_data(self, audio_data, sample_rate=None):
        """
        Set audio data for visualization

        Args:
            audio_data: numpy array of audio samples or list of floats
            sample_rate: sample rate (optional, for future use)
        """
        if audio_data is None:
            self.waveform_data = None
            self.update()
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

        self.waveform_data = audio_data
        self.update()

    def set_position(self, position):
        """
        Set current playback position

        Args:
            position: float from 0.0 to 1.0
        """
        self.current_position = max(0.0, min(1.0, position))
        if not self.is_dragging:  # Only update if not dragging
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), self.bg_color)

        width = self.width()
        height = self.height()
        center_y = height / 2

        # Draw center line
        painter.setPen(QPen(self.center_line_color, 1))
        painter.drawLine(0, int(center_y), width, int(center_y))

        if self.waveform_data is None or len(self.waveform_data) == 0:
            # Draw placeholder text
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, "No audio loaded"
            )
            return

        # Calculate how many samples to show per pixel
        samples_per_pixel = len(self.waveform_data) / width

        # Draw waveform
        self._draw_waveform(painter, width, height, center_y, samples_per_pixel)

        # Draw hover position line (when hovering but not dragging)
        if self.hover_position is not None and not self.is_dragging:
            hover_x = int(self.hover_position * width)
            painter.setPen(QPen(self.hover_line_color, 2))
            painter.drawLine(hover_x, 0, hover_x, height)

        # Draw current position line
        pos_x = int(self.current_position * width)
        painter.setPen(QPen(self.position_line_color, 2))
        painter.drawLine(pos_x, 0, pos_x, height)

    def _draw_waveform(self, painter, width, height, center_y, samples_per_pixel):
        """Draw the waveform with played/unplayed sections"""
        position_pixel = int(self.current_position * width)

        # Draw played portion (left of position line)
        if position_pixel > 0:
            path_played = self._create_waveform_path(
                0, position_pixel, center_y, samples_per_pixel
            )
            painter.setPen(QPen(self.waveform_played_color, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path_played)

        # Draw unplayed portion (right of position line)
        if position_pixel < width:
            path_unplayed = self._create_waveform_path(
                position_pixel, width, center_y, samples_per_pixel
            )
            painter.setPen(QPen(self.waveform_color, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path_unplayed)

    def _create_waveform_path(self, start_x, end_x, center_y, samples_per_pixel):
        """Create a QPainterPath for the waveform section"""
        path = QPainterPath()

        for x in range(start_x, end_x):
            # Calculate which samples this pixel represents
            sample_start = int(x * samples_per_pixel)
            sample_end = int((x + 1) * samples_per_pixel)

            if sample_end > len(self.waveform_data):
                sample_end = len(self.waveform_data)

            if sample_start >= len(self.waveform_data):
                break

            # Get min and max for this pixel's samples
            samples = self.waveform_data[sample_start:sample_end]
            if len(samples) == 0:
                continue

            min_val = np.min(samples)
            max_val = np.max(samples)

            # Scale to widget height (use 90% of height for amplitude)
            amplitude_scale = (self.height() / 2) * 0.9
            y_min = center_y - (min_val * amplitude_scale)
            y_max = center_y - (max_val * amplitude_scale)

            # Draw vertical line for this pixel
            if x == start_x:
                path.moveTo(x, y_max)
            else:
                path.lineTo(x, y_max)

            path.lineTo(x, y_min)

        return path

    def _get_position_from_mouse(self, event):
        """Calculate normalized position from mouse event"""
        x = event.position().x()
        return max(0.0, min(1.0, x / self.width()))

    def mousePressEvent(self, event):
        """Handle mouse press to start seeking"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            position = self._get_position_from_mouse(event)
            self.current_position = position
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self.seek_started.emit()
            self.position_moved.emit(position)
            self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging or hovering"""
        position = self._get_position_from_mouse(event)

        if self.is_dragging:
            # Update position while dragging
            self.current_position = position
            self.position_moved.emit(position)
            self.update()
        else:
            # Update hover position
            self.hover_position = position
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finish seeking"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            position = self._get_position_from_mouse(event)
            self.current_position = position
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.seek_finished.emit(position)
            self.update()

    def leaveEvent(self, event):
        """Handle mouse leaving the widget"""
        self.hover_position = None
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.update()

    def generate_sample_waveform(self, duration_seconds=10, sample_rate=44100):
        """Generate a sample waveform for testing"""
        t = np.linspace(0, duration_seconds, int(duration_seconds * sample_rate))
        # Create a complex waveform with multiple frequencies
        waveform = (
            np.sin(2 * np.pi * 440 * t) * 0.5
            + np.sin(2 * np.pi * 880 * t) * 0.3
            + np.sin(2 * np.pi * 220 * t) * 0.2
        )
        # Add some envelope
        envelope = np.exp(-t / duration_seconds * 2)
        waveform = waveform * envelope
        self.set_waveform_data(waveform, sample_rate)
