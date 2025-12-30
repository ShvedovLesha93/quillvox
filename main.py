import sys
from PySide6.QtWidgets import QApplication
from app.view_model.audio_player_vm import AudioPlayerVM
from app.view_model.file_selector import FileSelectorVM
from app.views.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")

    audio_vm = AudioPlayerVM()
    file_vm = FileSelectorVM(audio_vm)

    view = MainWindow(file_selector_vm=file_vm, audio_player_vm=audio_vm)

    view.show()
    sys.exit(app.exec())
