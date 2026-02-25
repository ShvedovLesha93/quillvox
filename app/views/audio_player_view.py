from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtGui import QFontMetrics, QCursor
from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
)
from PySide6.QtCore import Qt, Signal, Slot

from app.translator import language_manager, _
from app.constants import PlaybackState, ThemeMode
from app.utils.time_format import format_time
from app.views.waveform_view import WaveformView
from .ui_utils.icons import IconButton, IconLabel

if TYPE_CHECKING:
    from app.theme_manager import ThemeManager
    from app.view_model.waveform_vm import WaveformViewModel
    from app.view_model.audio_player_vm import AudioPlayerViewModel


class TimelineSlider(QSlider):
    hoverValueChanged = Signal(int)
    hoverLeft = Signal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._mouse_pressed = False
        self.time_label: QLabel | None = None
        self._label_parent: QWidget | None = None

    def set_time_label(self, label: QLabel) -> None:
        """Set external time label"""
        self.time_label = label
        parent = label.parent()
        if isinstance(parent, QWidget):
            self._label_parent = parent

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)

        if self.time_label is None or self._label_parent is None:
            return

        value = self._value_from_position(event.position())

        # Update label text and position
        self.time_label.setText(format_time(value, show_ms=True))
        self.time_label.adjustSize()

        # Calculate position with edge detection
        pos = event.position()
        label_width = self.time_label.width()
        slider_width = self.width()

        # Horizontal offset
        if pos.x() + 15 + label_width > slider_width:
            x_offset = -(label_width + 15)  # Left of cursor
        else:
            x_offset = 15  # Right of cursor

        # Vertical offset (always above slider handle)
        y_offset = 10

        # Map position from slider to parent widget coordinates
        global_pos = self.mapTo(self._label_parent, event.position().toPoint())

        self.time_label.move(
            int(global_pos.x() + x_offset), int(global_pos.y() + y_offset)
        )
        self.time_label.raise_()
        self.time_label.setVisible(True)

        if not self._mouse_pressed:
            self.hoverValueChanged.emit(value)

    def mousePressEvent(self, event) -> None:
        self._mouse_pressed = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._mouse_pressed = False
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event) -> None:
        if self.time_label:
            self.time_label.setVisible(False)
        self.hoverLeft.emit()
        return super().leaveEvent(event)

    def _value_from_position(self, pos) -> int:
        ratio = pos.x() / self.width()
        value = self.minimum() + ratio * (self.maximum() - self.minimum())
        return int(value)


class TruncatingLabel(QLabel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.full_text = ""

        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def setText(self, text: str) -> None:
        self.full_text = text
        self._update_text()

    def _update_text(self) -> None:
        if not self.full_text:
            super().setText("")
            self.setToolTip("")
            return

        fm = QFontMetrics(self.font())
        available_width = self.width()

        if available_width <= 0:
            return

        # Check if full text fits
        if fm.horizontalAdvance(self.full_text) <= available_width:
            super().setText(self.full_text)
            self.setToolTip("")

        else:
            # Calculate elided text
            elided = fm.elidedText(
                self.full_text, Qt.TextElideMode.ElideRight, available_width
            )
            super().setText(elided)

            # Set tooltip to show full text when truncated
            self.setToolTip(self.full_text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_text()


class AudioPlayer(QWidget):
    def __init__(
        self,
        audio_player_vm: AudioPlayerViewModel,
        waveform_vm: WaveformViewModel,
        theme_manager: ThemeManager,
    ) -> None:
        super().__init__()
        self.audio_player_vm = audio_player_vm
        self.waveform_vm = waveform_vm
        self.theme_manager = theme_manager

        self.volume_before_mute: int

        self._setup_ui()
        self._connect_signals()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        btn_layout = QHBoxLayout()
        timeline_layout = QHBoxLayout()

        control_layout = QHBoxLayout()

        # File name
        self.file_name = TruncatingLabel(self)
        self.file_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Wave visualizer
        self.waveform_view = WaveformView(
            waveform_vm=self.waveform_vm, theme_manager=self.theme_manager, parent=self
        )

        # Playback buttons
        self.play_btn = IconButton(name="play_arrow", scale=0.8)
        self.play_btn.setEnabled(False)

        self.stop_btn = IconButton(name="stop")
        self.stop_btn.setEnabled(False)

        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)

        timeline_layout.addLayout(btn_layout)

        # Timeline slider
        self.timeline_slider = TimelineSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.setMouseTracking(False)

        self.timeline_label = QLabel(self)
        self.timeline_label.setObjectName("timelineLabel")
        self.timeline_label.raise_()
        self.timeline_label.setVisible(False)
        self.timeline_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.timeline_slider.set_time_label(self.timeline_label)

        # Time labels
        self.current_time_label = QLabel("00:00")
        self.total_label = QLabel("00:00")

        timeline_layout.addWidget(self.current_time_label)
        timeline_layout.addWidget(self.timeline_slider)
        timeline_layout.addWidget(self.total_label)

        # Playback controls

        # Volume control
        self.volume_btn = IconButton(name="volume_up")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(150)
        self.volume_value_label = QLabel("50%")
        self.volume_value_label.setMinimumWidth(30)

        control_layout.addWidget(self.volume_btn)
        control_layout.addWidget(self.volume_slider)
        control_layout.addWidget(self.volume_value_label)

        # Speed control
        self.speed_label = IconLabel("speed")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(25, 200)  # 0.25x to 2.0x speed
        self.speed_slider.setValue(100)  # Default speed 1.0x
        self.speed_slider.setFixedWidth(150)
        self.speed_value_label = QLabel("1.00x")
        self.speed_value_label.setMinimumWidth(35)
        self.speed_reset_btn = IconButton(name="replay", scale=0.8)
        self.speed_reset_btn.setMaximumWidth(60)
        self.speed_reset_btn.setEnabled(False)

        # Add speed components to layout
        control_layout.addWidget(self.speed_label)
        control_layout.addWidget(self.speed_slider)
        control_layout.addWidget(self.speed_value_label)
        control_layout.addWidget(self.speed_reset_btn)
        control_layout.addStretch()

        layout.addWidget(self.file_name)
        layout.addWidget(self.waveform_view)
        layout.addLayout(timeline_layout)
        layout.addLayout(control_layout)

        self.speed_slider.valueChanged.connect(self._on_speed_changed)

    def _on_speed_changed(self, value: int) -> None:
        self.speed_reset_btn.setEnabled(not value == 100)

    def retranslate(self) -> None:
        self.file_name.setText(_("No file opened"))

    def _connect_signals(self) -> None:
        # =========== UI → AudioPlayerViewModel ============
        self.play_btn.clicked.connect(self.audio_player_vm.toggle_play)
        self.stop_btn.clicked.connect(self.audio_player_vm.stop)
        self.volume_btn.clicked.connect(
            lambda: self._on_volume_clicked(self.volume_slider.value())
        )

        # Timeline slider
        self.timeline_slider.sliderPressed.connect(self.audio_player_vm.begin_seek)
        self.timeline_slider.sliderReleased.connect(
            lambda: self.audio_player_vm.end_seek(self.timeline_slider.value())
        )
        self.timeline_slider.sliderMoved.connect(self.audio_player_vm.seek_to)
        self.timeline_slider.hoverValueChanged.connect(
            self.audio_player_vm.hover_seek_to
        )
        self.timeline_slider.hoverLeft.connect(self.audio_player_vm.hover_end_seek)

        # Controls

        # Volume control
        self.volume_slider.valueChanged.connect(self.audio_player_vm.set_volume)

        # Speed control
        self.speed_slider.valueChanged.connect(self.audio_player_vm.set_speed)
        self.speed_reset_btn.clicked.connect(self._on_speed_reset_btn_clicked)

        # =========== AudioPlayerViewModel → UI ===========
        self.audio_player_vm.duration_changed.connect(self._on_duration_changed)
        self.audio_player_vm.position_changed.connect(self._on_position_changed)

        self.audio_player_vm.str_current_time_changed.connect(
            self.current_time_label.setText
        )
        self.audio_player_vm.str_total_time_changed.connect(self.total_label.setText)
        self.audio_player_vm.str_speed_changed.connect(self.speed_value_label.setText)
        self.audio_player_vm.int_volume_changed.connect(self._on_volume_changed)

        self.audio_player_vm.playback_state_changed.connect(self._on_playback_state)
        self.audio_player_vm.file_loaded.connect(self._on_file_loaded)

        # =========== WaveformViewModel → UI ===========
        self.waveform_vm.waveform_loaded.connect(self.waveform_view.load_waveform)
        self.waveform_view.position_changed.connect(self.audio_player_vm.set_position)
        self.waveform_view.hover_position_changed.connect(
            self.audio_player_vm.hover_seek_to
        )
        self.waveform_view.hover_left.connect(self.audio_player_vm.hover_end_seek)

    @Slot(int)
    def _on_duration_changed(self, value: int) -> None:
        self.timeline_slider.setRange(0, value)
        self.waveform_view.duration = value

    @Slot(int)
    def _on_position_changed(self, value: int) -> None:
        if not self.timeline_slider.isSliderDown():
            self.timeline_slider.setValue(value)
            self.waveform_view.set_position(value)

    def _on_volume_clicked(self, value: int) -> None:
        def set_slider_volume(value: int) -> None:
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(value)
            self.volume_slider.blockSignals(False)

        if value > 0:
            self.volume_before_mute = value
            self.volume_btn.set_icon(icon="volume_off")
            set_slider_volume(0)
            self.audio_player_vm.set_volume(0)
        else:
            self.volume_btn.set_icon(icon="volume_up")
            set_slider_volume(self.volume_before_mute)

            self.audio_player_vm.set_volume(self.volume_before_mute)

    def _on_volume_changed(self, value: int) -> None:
        self.volume_value_label.setText(f"{value}%")
        icon = "volume_off" if value == 0 else "volume_up"
        self.volume_btn.set_icon(icon)

    def _on_file_loaded(self, file: str) -> None:
        self.timeline_slider.setMouseTracking(True)
        self.file_name.setText(file)
        self.play_btn.setEnabled(True)

    def _on_speed_reset_btn_clicked(self) -> None:
        self.speed_slider.setValue(100)
        self.audio_player_vm.reset_speed()
        self.speed_value_label.setText("1.00x")

    def _on_playback_state(self, state: PlaybackState) -> None:
        if state == PlaybackState.PLAYING:
            self.play_btn.set_icon(icon="pause")
            self.stop_btn.setEnabled(True)

        elif state == PlaybackState.PAUSED:
            self.play_btn.set_icon(icon="play_arrow")

        else:
            self.play_btn.set_icon(icon="play_arrow")
            self.stop_btn.setEnabled(state != PlaybackState.STOPPED)


# ============ TEST ============
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from pathlib import Path
    from app.view_model.audio_player_vm import AudioPlayerViewModel
    from app.view_model.waveform_vm import WaveformViewModel
    from app.theme_manager import ThemeManager

    app = QApplication([])
    app.setStyle("Fusion")

    waveform_vm = WaveformViewModel()
    audio_player_vm = AudioPlayerViewModel(waveform_vm)
    theme_manager = ThemeManager(app, ThemeMode.DARK)

    view = AudioPlayer(
        audio_player_vm=audio_player_vm,
        waveform_vm=waveform_vm,
        theme_manager=theme_manager,
    )
    view.resize(300, 150)
    view.move(1020, 320)

    audio = Path("tests/audio/LJ025-0076.wav")
    long_audio = Path("tests/_local/long_audio.m4a")
    if audio.exists():
        view.audio_player_vm.load(audio)
    else:
        print(f"Error: File '{audio.name}' not found")

    view.show()
    app.exec()
