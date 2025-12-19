from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QApplication


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    view = MainWindow()

    view.show()
    app.exec()
