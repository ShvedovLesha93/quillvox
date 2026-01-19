from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
)

from app.view_model.stt_settings_vm import Category
from app.views.ui_utils.title import Title
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.view_model.stt_settings_vm import STTSettingsViewModel


class STTSettings(QWidget):
    def __init__(self, settings_vm: STTSettingsViewModel) -> None:
        super().__init__()
        self.vm = settings_vm

        self._setup_ui()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(10)

        form_layout = QFormLayout()

        # Title
        self.title = Title(self)
        main_layout.addWidget(self.title)

        main_layout.addLayout(form_layout)

        main_layout.addStretch()

        # Model
        model_combo = QComboBox()
        self.model_label = QLabel()
        form_layout.addRow(self.model_label, model_combo)
        self.add_combo(model_combo, Category.MODEL)

        # Device
        device_combo = QComboBox()
        self.device_label = QLabel()
        form_layout.addRow(self.device_label, device_combo)
        self.add_combo(device_combo, Category.DEVICE)

        # Compute type
        compute_type_combo = QComboBox()
        self.compute_type_label = QLabel()
        form_layout.addRow(self.compute_type_label, compute_type_combo)
        self.add_combo(compute_type_combo, Category.COMPUTE_TYPE)

        # Batch size
        batch_size_combo = QComboBox()
        self.batch_size_label = QLabel()
        form_layout.addRow(self.batch_size_label, batch_size_combo)
        self.add_combo(batch_size_combo, Category.BATCH_SIZE)

        # Language
        lang_combo = QComboBox()
        self.lang_label = QLabel()
        form_layout.addRow(self.lang_label, lang_combo)
        self.add_combo(lang_combo, Category.LANGUAGE)

        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content_widget)

        outer_layout.addWidget(scroll)

    def retranslate(self) -> None:
        self.model_label.setText(_("Model"))
        self.device_label.setText(_("Device"))
        self.lang_label.setText(_("Language"))
        self.compute_type_label.setText(_("Compute type"))
        self.batch_size_label.setText(_("Batch size"))
        self.title.setTitle(_("Transcription"))

    def add_combo(self, combo: QComboBox, category: Category) -> None:
        # combo.blockSignals(True)
        for key, label in self.vm.get_labels(category).items():
            combo.addItem(label, key)

        combo.setCurrentIndex(combo.findData(self.vm.get_current(category)))

        combo.currentIndexChanged.connect(
            lambda i: self.vm.set_current(category=category, key=combo.itemData(i))
        )
        # combo.blockSignals(False)
