from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
)

from app.view_model.stt_settings_vm import Category
from app.views.ui_utils.icons import IconButton, IconName
from app.views.ui_utils.title import Title
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.view_model.stt_settings_vm import STTSettingsViewModel


class ResetButton(IconButton):
    def __init__(self, _parent: STTSettings, category: Category):
        super().__init__(name=IconName.REPLAY, scale=0.7, parent=None)
        self._parent = _parent
        self.category = category
        self._setup_ui()

    def _setup_ui(self):
        self.setVisible(False)
        self.setFixedSize(25, 25)
        self.setToolTip("Reset to default")
        self.clicked.connect(lambda: self._parent._reset_parameter(self.category))

    def create_container(self):
        """Create a container widget that reserves space for this button"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self)
        container.setFixedWidth(30)
        return container


@dataclass
class RowOptions:
    label: dict = field(default_factory=dict[Category, QLabel])
    combo: dict = field(default_factory=dict[Category, QComboBox])
    reset_btn: dict = field(default_factory=dict[Category, ResetButton])


class STTSettings(QWidget):
    def __init__(self, general_settings_vm: STTSettingsViewModel) -> None:
        super().__init__()
        self.vm = general_settings_vm

        self._row_options = RowOptions()

        self._setup_ui()
        self._connect_signals()

        self.retranslate()

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(10)

        self.grid_layout = QGridLayout()
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 0)
        self.grid_layout.setColumnStretch(2, 0)
        self.grid_layout.setColumnStretch(3, 0)
        self.grid_layout.setColumnStretch(4, 1)

        form_layout = QFormLayout()

        # Title
        self.title = Title(self)
        main_layout.addWidget(self.title)

        main_layout.addLayout(self.grid_layout)
        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        # Parameters
        self.add_option_row(1, Category.MODEL)
        self.add_option_row(2, Category.DEVICE)
        self.add_option_row(3, Category.COMPUTE_TYPE)
        self.add_option_row(4, Category.BATCH_SIZE)
        self.add_option_row(5, Category.LANGUAGE)

        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content_widget)

        outer_layout.addWidget(scroll)

    def retranslate(self) -> None:
        label: QLabel
        for category, label in self._row_options.label.items():
            match category:
                case Category.MODEL:
                    label.setText(_("Model"))
                case Category.DEVICE:
                    label.setText(_("Device"))
                case Category.COMPUTE_TYPE:
                    label.setText(_("Compute type"))
                case Category.BATCH_SIZE:
                    label.setText(_("Batch size"))
                case Category.LANGUAGE:
                    label.setText(_("Transcription language"))
        self.title.setTitle(_("Transcription"))

    def _connect_signals(self) -> None:
        language_manager.language_changed.connect(self.retranslate)
        self.vm.settings_vm.restore_requested.connect(self.restore_currents)
        self.vm.saved.connect(self._reset_ui)

    @Slot()
    def _reset_ui(self) -> None:
        reset_btn = self._row_options.reset_btn
        for btn in reset_btn.values():
            btn.setVisible(False)

    @Slot(int, object)
    def _on_parameter_changed(self, index: int, category: Category) -> None:
        combo = self._row_options.combo[category]
        key = combo.itemData(index)
        is_changed = self.vm.parameter_changed(category=category, key=key)
        reset_btn = self._row_options.reset_btn[category]
        reset_btn.setVisible(not is_changed)

    @Slot(object)
    def _reset_parameter(self, category: Category) -> None:
        current_key = self.vm.get_current(category)
        combo = self._row_options.combo[category]
        combo.setCurrentIndex(combo.findData(current_key))

    def add_option_row(self, row: int, category: Category) -> None:
        label = QLabel()
        combo = QComboBox()
        reset_btn = ResetButton(self, category)

        self._row_options.label[category] = label
        self._row_options.combo[category] = combo
        self._row_options.reset_btn[category] = reset_btn

        reset_btn_container = reset_btn = reset_btn.create_container()

        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.grid_layout.addWidget(label, row, 1)
        self.grid_layout.addWidget(combo, row, 2)
        self.grid_layout.addWidget(reset_btn_container, row, 3)

        self.add_combo_data(combo, category)

        combo.currentIndexChanged.connect(
            lambda i: self._on_parameter_changed(i, category)
        )

    def add_combo_data(self, combo: QComboBox, category: Category) -> None:
        combo.blockSignals(True)

        for key, label in self.vm.get_labels(category).items():
            combo.addItem(label, key)

        current = self.vm.get_current(category)
        combo.setCurrentIndex(combo.findData(current))

        combo.currentIndexChanged.connect(
            lambda i: self.vm.setings_changed(category=category, key=combo.itemData(i))
        )
        combo.blockSignals(False)

    @Slot()
    def restore_currents(self) -> None:
        for category, combo in self._row_options.combo.items():
            combo.setCurrentIndex(combo.findData(self.vm.get_current(category)))
