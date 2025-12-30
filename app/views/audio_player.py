from typing import TYPE_CHECKING
from PySide6.QtWidgets import (
    QGridLayout,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
)
from PySide6.QtCore import Qt

from app.constants import PlaybackState

if TYPE_CHECKING:
    from app.view_model.audio_player_vm import AudioPlayerVM


class AudioPlayer(QWidget):
    def __init__(self, audio_player_view_model: "AudioPlayerVM") -> None:
        super().__init__()
        self.vm = audio_player_view_model

        self._setup_ui()
        self._bind_vm()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        timeline_layout = QHBoxLayout()
        control_layout = QGridLayout()

        control_layout.setColumnStretch(0, 0)
        control_layout.setColumnStretch(1, 0)
        control_layout.setColumnStretch(2, 0)
        control_layout.setColumnStretch(3, 0)
        control_layout.setColumnStretch(4, 1)

        # Playback buttons
        self.play_btn = QPushButton("Play")
        self.play_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)

        btn_layout.addStretch()
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()

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
        self.volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(150)
        self.volume_value_label = QLabel("50%")
        self.volume_value_label.setMinimumWidth(30)

        control_layout.addWidget(self.volume_label, 0, 0)
        control_layout.addWidget(self.volume_slider, 0, 1)
        control_layout.addWidget(self.volume_value_label, 0, 2)

        # Speed control
        self.speed_label = QLabel("Speed:")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(25, 200)  # 0.25x to 2.0x speed
        self.speed_slider.setValue(100)  # Default speed 1.0x
        self.speed_slider.setFixedWidth(150)
        self.speed_value_label = QLabel("1.00x")
        self.speed_value_label.setMinimumWidth(35)
        self.speed_reset_btn = QPushButton("Reset")
        self.speed_reset_btn.setMaximumWidth(60)

        # Add speed components to layout
        control_layout.addWidget(self.speed_label, 1, 0)
        control_layout.addWidget(self.speed_slider, 1, 1)
        control_layout.addWidget(self.speed_value_label, 1, 2)
        control_layout.addWidget(self.speed_reset_btn, 1, 3)

        layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addLayout(timeline_layout)
        layout.addLayout(control_layout)

    def _bind_vm(self) -> None:
        # =========== UI → ViewModel ============
        self.play_btn.clicked.connect(self.vm.toggle_play)
        self.stop_btn.clicked.connect(self.vm.stop)

        # Timeline slider
        self.timeline_slider.sliderPressed.connect(self.vm.begin_seek)
        self.timeline_slider.sliderReleased.connect(
            lambda: self.vm.end_seek(self.timeline_slider.value())
        )
        self.timeline_slider.sliderMoved.connect(self.vm.seek_to)

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
        self.vm.str_volume_changed.connect(self.volume_value_label.setText)
        self.vm.str_speed_changed.connect(self.speed_value_label.setText)

        self.vm.playback_state_changed.connect(self._on_playback_state)
        self.vm.file_loaded.connect(lambda: self.play_btn.setEnabled(True))

    def _on_speed_reset_btn_clicked(self) -> None:
        self.vm.set_speed(100)
        self.speed_value_label.setText("1.00x")
        self.speed_slider.setValue(100)

    def _on_playback_state(self, state: PlaybackState) -> None:
        if state == PlaybackState.PLAYING:
            self.play_btn.setText("Pause")
            self.stop_btn.setEnabled(True)

        elif state == PlaybackState.PAUSED:
            self.play_btn.setText("Play")

        else:
            self.play_btn.setText("Play")
            self.stop_btn.setEnabled(state != PlaybackState.STOPPED)


# ============ TEST ============
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from pathlib import Path
    from app.view_model.audio_player_vm import AudioPlayerVM

    app = QApplication([])
    app.setStyle("Fusion")

    view = AudioPlayer(AudioPlayerVM())
    view.play_btn.setEnabled(True)
    view.resize(300, 150)
    view.move(1020, 320)

    audio = Path("tests/audio/LJ025-0076.wav")
    if audio.exists():
        view.vm.load(audio)
        view.show()
        app.exec()
    else:
        print(f"Error: File '{audio.name}' not found")
