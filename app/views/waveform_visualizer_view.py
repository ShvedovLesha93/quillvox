from pathlib import Path
import librosa
import pyqtgraph as pg
from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout
import numpy as np


class WaveformDataWorker(QObject):
    """Worker for loading and processing audio data in background thread"""

    finished = Signal(object, object)  # (x_data, waveform_data)
    error = Signal(str)

    def __init__(self, file: Path, max_samples: int = 1000000) -> None:
        super().__init__()
        self.file = file
        self.max_samples = max_samples

    def run(self):
        """Load audio file and process waveform data"""
        try:
            # Load audio file using librosa
            audio_data, _ = librosa.load(str(self.file), sr=None, mono=True)

            # Normalize
            if audio_data.max() > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            # Downsample if needed to save memory
            if len(audio_data) > self.max_samples:
                # Use min/max downsampling to preserve waveform peaks
                chunk_size = len(audio_data) // (self.max_samples // 2)
                downsampled = []
                x_vals = []

                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i : i + chunk_size]
                    if len(chunk) > 0:
                        min_idx = np.argmin(chunk)
                        max_idx = np.argmax(chunk)

                        if min_idx < max_idx:
                            downsampled.extend([chunk[min_idx], chunk[max_idx]])
                            x_vals.extend([i + min_idx, i + max_idx])
                        else:
                            downsampled.extend([chunk[max_idx], chunk[min_idx]])
                            x_vals.extend([i + max_idx, i + min_idx])

                waveform_data = np.array(downsampled, dtype=np.float32)
                x_data = np.array(x_vals, dtype=np.int32)
            else:
                waveform_data = audio_data.astype(np.float32)
                x_data = np.arange(len(audio_data), dtype=np.int32)

            # Emit the processed data
            self.finished.emit(x_data, waveform_data)

        except Exception as e:
            self.error.emit(str(e))


class WaveformVisualizer(QWidget):
    """High-performance waveform visualizer using PyQtGraph's built-in optimizations"""

    seek_started = Signal()
    position_moved = Signal(float)
    seek_finished = Signal(float)
    loading_finished = Signal()
    loading_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_data = None
        self.original_length = 0
        self.current_position = 0.0
        self.is_dragging = False

        self.setMinimumHeight(80)
        self.setMaximumHeight(120)

        self._setup_ui()

        self._thread: QThread | None = None
        self._worker: WaveformDataWorker | None = None

    def _setup_ui(self):
        """Initialize PyQtGraph plot widget with built-in optimizations"""
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
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.plot_widget.setContentsMargins(0, 0, 0, 0)

        # Get ViewBox for custom zoom behavior
        self.view_box = self.plot_widget.getViewBox()
        self.view_box.setMouseEnabled(
            x=True, y=False
        )  # Allow horizontal panning/zooming
        self.view_box.setLimits(yMin=-1.2, yMax=1.2)  # Limit Y axis

        # Create single waveform plot
        self.waveform = self.plot_widget.plot(
            pen=pg.mkPen(color=(100, 180, 255), width=1)
        )

        # Enable PyQtGraph's built-in optimizations
        self.waveform.setDownsampling(auto=True, method="peak")
        self.waveform.setClipToView(True)

        # Create position line
        self.position_line = pg.InfiniteLine(
            pos=0, angle=90, pen=pg.mkPen(color=(255, 100, 100), width=2), movable=False
        )
        self.position_line.setVisible(False)
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

        layout.addWidget(self.plot_widget)

        # Connect mouse events
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_move)  # type: ignore
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)  # type: ignore
        self.plot_widget.viewport().installEventFilter(self)

    def load_waveform_data(self, audio: Path) -> None:
        """Load waveform data in background thread"""
        # Clean up previous thread if exists
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()

        # Create new thread and worker
        self._thread = QThread()
        self._worker = WaveformDataWorker(audio)
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_waveform_loaded)
        self._worker.error.connect(self._on_loading_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        # Start loading
        self._thread.start()

    def reset(self) -> None:
        """Reset the visualizer to empty state"""
        self.x_data = None
        self.original_length = 0
        self.current_position = 0.0
        self.waveform.setData([])
        self.position_line.setPos(0)
        self.position_line.setEnabled(False)

    def set_position(self, position):
        """Set current playback position (0.0 to 1.0)"""
        self.current_position = max(0.0, min(1.0, position))

        if not self.is_dragging and self.original_length > 0:
            # Just update position line - waveform stays stable
            pos_sample = int(self.current_position * self.original_length)
            self.position_line.setPos(pos_sample)

    def _on_waveform_loaded(self, x_data, waveform_data):
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

    def _on_loading_error(self, error_msg: str):
        """Callback when loading fails"""
        self.loading_error.emit(error_msg)

    def _get_position_from_scene(self, scene_pos):
        """Convert scene position to normalized position (0.0 to 1.0)"""
        if self.original_length == 0:
            return 0.0

        mouse_point = self.view_box.mapSceneToView(scene_pos)
        x = mouse_point.x()

        # x is in original sample coordinates
        position = x / self.original_length if self.original_length > 0 else 0.0
        return max(0.0, min(1.0, position))

    def _on_mouse_move(self, pos):
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

    def _on_mouse_click(self, event):
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
