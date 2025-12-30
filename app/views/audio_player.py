from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
)
from PySide6.QtCore import Qt

from app.view_model.audio_player_vm import PlayerViewModel
from app.constants import PlaybackState


class AudioPlayer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.vm = PlayerViewModel(self)

        self._setup_ui()
        self._bind_vm()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        timeline_layout = QHBoxLayout()

        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)

        btn_layout.addStretch()
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)

        self.current_label = QLabel("00:00")
        self.total_label = QLabel("00:00")

        timeline_layout.addWidget(self.current_label)
        timeline_layout.addWidget(self.slider)
        timeline_layout.addWidget(self.total_label)

        layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addLayout(timeline_layout)

    def _bind_vm(self) -> None:
        # UI → VM
        self.play_btn.clicked.connect(self.vm.toggle_play)
        self.stop_btn.clicked.connect(self.vm.stop)

        self.slider.sliderPressed.connect(self.vm.begin_seek)
        self.slider.sliderReleased.connect(
            lambda: self.vm.end_seek(self.slider.value())
        )
        self.slider.sliderMoved.connect(self.vm.seek_to)

        # VM → UI
        self.vm.duration_changed.connect(lambda d: self.slider.setRange(0, d))
        self.vm.position_changed.connect(
            lambda p: not self.slider.isSliderDown() and self.slider.setValue(p)
        )

        self.vm.current_time_text_changed.connect(self.current_label.setText)
        self.vm.total_time_text_changed.connect(self.total_label.setText)

        self.vm.playback_state_changed.connect(self._on_playback_state)

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

    app = QApplication([])
    app.setStyle("Fusion")

    view = AudioPlayer()
    view.move(1020, 320)

    audio = Path("tests/audio/LJ025-0076.wav")
    if audio.exists():
        view.vm.load(audio)
        view.show()
        app.exec()
    else:
        print(f"Error: File '{audio.name}' not found")
