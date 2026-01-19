from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
)
from PySide6.QtCore import Qt
import librosa

from app.translator import language_manager, _
from app.constants import PlaybackState
from app.views.waveform_visualizer_view import WaveformVisualizer
from .ui_utils.icons import IconButton, IconLabel, IconName


if TYPE_CHECKING:
    from app.view_model.audio_player_vm import AudioPlayerViewModel


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
    def __init__(self, audio_player_view_model: "AudioPlayerViewModel") -> None:
        super().__init__()
        self.vm = audio_player_view_model
        self.volume_before_mute: int

        self._setup_ui()
        self._bind_vm()

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
        self.audio_visualizer_widget = WaveformVisualizer(self)
        self.audio_visualizer_widget.seek_started.connect(
            self._on_visualizer_seek_started
        )
        self.audio_visualizer_widget.position_moved.connect(
            self._on_visualizer_position_moved
        )
        self.audio_visualizer_widget.seek_finished.connect(
            self._on_visualizer_seek_finished
        )

        # Playback buttons
        self.play_btn = IconButton(IconName.PLAY_ARROW, 0.8)
        self.play_btn.setEnabled(False)

        self.stop_btn = IconButton(IconName.STOP)
        self.stop_btn.setEnabled(False)

        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)

        timeline_layout.addLayout(btn_layout)

        # Timeline slider
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)

        # Time labels
        self.current_time_label = QLabel("00:00")
        self.total_label = QLabel("00:00")

        timeline_layout.addWidget(self.current_time_label)
        timeline_layout.addWidget(self.timeline_slider)
        timeline_layout.addWidget(self.total_label)

        # Playback controls

        # Volume control
        self.volume_btn = IconButton(IconName.VOLUME_UP)
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
        self.speed_label = IconLabel(IconName.SPEED)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(25, 200)  # 0.25x to 2.0x speed
        self.speed_slider.setValue(100)  # Default speed 1.0x
        self.speed_slider.setFixedWidth(150)
        self.speed_value_label = QLabel("1.00x")
        self.speed_value_label.setMinimumWidth(35)
        self.speed_reset_btn = IconButton(IconName.REPLAY, scale=0.8)
        self.speed_reset_btn.setMaximumWidth(60)
        self.speed_reset_btn.setEnabled(False)

        # Add speed components to layout
        control_layout.addWidget(self.speed_label)
        control_layout.addWidget(self.speed_slider)
        control_layout.addWidget(self.speed_value_label)
        control_layout.addWidget(self.speed_reset_btn)
        control_layout.addStretch()

        layout.addWidget(self.file_name)
        layout.addWidget(self.audio_visualizer_widget)
        layout.addLayout(timeline_layout)
        layout.addLayout(control_layout)

        self.speed_slider.valueChanged.connect(self._on_speed_changed)

    def _on_speed_changed(self, value: int) -> None:
        self.speed_reset_btn.setEnabled(not value == 100)

    def retranslate(self) -> None:
        self.file_name.setText(_("No file opened"))

    def _bind_vm(self) -> None:
        # =========== UI → ViewModel ============
        self.play_btn.clicked.connect(self.vm.toggle_play)
        self.stop_btn.clicked.connect(self.vm.stop)
        self.volume_btn.clicked.connect(
            lambda: self._on_volume_clicked(self.volume_slider.value())
        )

        # Timeline slider
        self.timeline_slider.sliderPressed.connect(self.vm.begin_seek)
        self.timeline_slider.sliderReleased.connect(
            lambda: self.vm.end_seek(self.timeline_slider.value())
        )
        self.timeline_slider.sliderMoved.connect(self.vm.seek_to)
        self.timeline_slider.valueChanged.connect(self._update_visualizer_position)

        # Controls

        # Volume control
        self.volume_slider.valueChanged.connect(self.vm.set_volume)

        # Speed control
        self.speed_slider.valueChanged.connect(self.vm.set_speed)
        self.speed_reset_btn.clicked.connect(self._on_speed_reset_btn_clicked)

        # =========== ViewModel → UI ===========
        self.vm.duration_changed.connect(lambda d: self.timeline_slider.setRange(0, d))
        self.vm.position_changed.connect(
            lambda p: not self.timeline_slider.isSliderDown()
            and self.timeline_slider.setValue(p)
        )

        self.vm.str_current_time_changed.connect(self.current_time_label.setText)
        self.vm.str_total_time_changed.connect(self.total_label.setText)
        self.vm.str_speed_changed.connect(self.speed_value_label.setText)
        self.vm.int_volume_changed.connect(self._on_volume_changed)

        self.vm.playback_state_changed.connect(self._on_playback_state)
        self.vm.file_loaded.connect(self._on_file_loaded)

    def _on_volume_clicked(self, value: int) -> None:
        def set_slider_volume(value: int) -> None:
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(value)
            self.volume_slider.blockSignals(False)

        if value > 0:
            self.volume_before_mute = value
            self.volume_btn.set_icon(IconName.VOLUME_OFF)
            set_slider_volume(0)
            self.vm.set_volume(0)
        else:
            self.volume_btn.set_icon(IconName.VOLUME_UP)
            set_slider_volume(self.volume_before_mute)

            self.vm.set_volume(self.volume_before_mute)

    def _on_volume_changed(self, value: int) -> None:
        self.volume_value_label.setText(f"{value}%")
        icon = IconName.VOLUME_OFF if value == 0 else IconName.VOLUME_UP
        self.volume_btn.set_icon(icon)

    def _on_file_loaded(self, name: str) -> None:
        self.file_name.setText(name)
        self.play_btn.setEnabled(True)
        audio_data, sr = self.vm.load_waveform_data()
        self.audio_visualizer_widget.set_waveform_data(audio_data, sr)
        # self.audio_visualizer_widget.generate_sample_waveform()

    def _on_speed_reset_btn_clicked(self) -> None:
        self.speed_slider.setValue(100)
        self.vm.reset_speed()
        self.speed_value_label.setText("1.00x")

    def _on_playback_state(self, state: PlaybackState) -> None:
        if state == PlaybackState.PLAYING:
            self.play_btn.set_icon(IconName.PAUSE)
            self.stop_btn.setEnabled(True)

        elif state == PlaybackState.PAUSED:
            self.play_btn.set_icon(IconName.PLAY_ARROW)

        else:
            self.play_btn.set_icon(IconName.PLAY_ARROW)
            self.stop_btn.setEnabled(state != PlaybackState.STOPPED)

    def _update_visualizer_position(self):
        """Update visualizer position when timeline slider changes"""
        if self.timeline_slider.maximum() > 0:
            position = self.timeline_slider.value() / self.timeline_slider.maximum()
            self.audio_visualizer_widget.set_position(position)

    def _on_visualizer_clicked(self, position):
        """Handle clicks on the visualizer to seek"""
        if self.timeline_slider.maximum() > 0:
            new_value = int(position * self.timeline_slider.maximum())
            self.timeline_slider.setValue(new_value)

    def _on_visualizer_seek_started(self):
        """Called when user starts dragging on visualizer"""
        self.vm.begin_seek()

    def _on_visualizer_position_moved(self, position):
        """Called while user is dragging on visualizer"""
        if self.timeline_slider.maximum() > 0:
            new_value = int(position * self.timeline_slider.maximum())
            self.vm.seek_to(new_value)

    def _on_visualizer_seek_finished(self, position):
        """Called when user releases drag on visualizer"""
        if self.timeline_slider.maximum() > 0:
            new_value = int(position * self.timeline_slider.maximum())
            self.vm.end_seek(new_value)


# ============ TEST ============
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from pathlib import Path
    from app.view_model.audio_player_vm import AudioPlayerViewModel

    app = QApplication([])
    app.setStyle("Fusion")

    view = AudioPlayer(AudioPlayerViewModel())
    view.resize(300, 150)
    view.move(1020, 320)

    audio = Path("tests/audio/LJ025-0076.wav")
    if audio.exists():
        view.vm.load(audio)
    else:
        print(f"Error: File '{audio.name}' not found")

    view.show()
    app.exec()
