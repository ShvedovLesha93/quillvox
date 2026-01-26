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

from app.view_model.stt_settings_vm import STTSettingCategory
from app.views.ui_utils.icons import IconButton, IconName
from app.views.ui_utils.title import Title
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.view_model.stt_settings_vm import STTSettingsViewModel


class ResetButton(IconButton):
    def __init__(self, _parent: STTSettingsView, category: STTSettingCategory):
        super().__init__(name=IconName.REPLAY, scale=0.7, parent=None)
        self._parent = _parent
        self.category = category
        self._setup_ui()

    def _setup_ui(self):
        self.setVisible(False)
        self.setFixedSize(25, 25)
        self.setToolTip("Reset to default")
        self.clicked.connect(lambda: self._parent._discard_value(self.category))

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
    label: dict = field(default_factory=dict[STTSettingCategory, QLabel])
    combo: dict = field(default_factory=dict[STTSettingCategory, QComboBox])
    reset_btn: dict = field(default_factory=dict[STTSettingCategory, ResetButton])


class STTSettingsView(QWidget):
    def __init__(self, stt_settings_vm: STTSettingsViewModel) -> None:
        super().__init__()
        self.vm = stt_settings_vm

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
        self.add_option_row(1, STTSettingCategory.MODEL)
        self.add_option_row(2, STTSettingCategory.DEVICE)
        self.add_option_row(3, STTSettingCategory.COMPUTE_TYPE)
        self.add_option_row(4, STTSettingCategory.BATCH_SIZE)
        self.add_option_row(5, STTSettingCategory.LANGUAGE)

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
                case STTSettingCategory.MODEL:
                    label.setText(_("Model"))
                case STTSettingCategory.DEVICE:
                    label.setText(_("Device"))
                case STTSettingCategory.COMPUTE_TYPE:
                    label.setText(_("Compute type"))
                case STTSettingCategory.BATCH_SIZE:
                    label.setText(_("Batch size"))
                case STTSettingCategory.LANGUAGE:
                    label.setText(_("Transcription language"))
        self.title.setTitle(_("Transcription"))

    def _connect_signals(self) -> None:
        language_manager.language_changed.connect(self.retranslate)
        self.vm.settings_vm.restore_requested.connect(self.discard_settings)
        self.vm.saved.connect(self._reset_ui)

    @Slot()
    def _reset_ui(self) -> None:
        reset_btn = self._row_options.reset_btn
        for btn in reset_btn.values():
            btn.setVisible(False)

    @Slot(int, object)
    def _on_index_changed(self, category: STTSettingCategory, value) -> None:
        is_changed = self.vm.on_value_changed(category=category, new_value=value)
        reset_btn = self._row_options.reset_btn[category]
        reset_btn.setVisible(is_changed)

    @Slot(object)
    def _discard_value(self, category: STTSettingCategory) -> None:
        current_key = self.vm.get_current_value(category)
        combo = self._row_options.combo[category]
        combo.setCurrentIndex(combo.findData(current_key))

    def add_option_row(self, row: int, category: STTSettingCategory) -> None:
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

    def add_combo_data(self, combo: QComboBox, category: STTSettingCategory) -> None:

        combo.blockSignals(True)

        for key, label in self.vm.get_labels(category).items():
            combo.addItem(label, key)

        current = self.vm.get_current_value(category)
        combo.setCurrentIndex(combo.findData(current))

        combo.currentIndexChanged.connect(
            lambda i: self._on_index_changed(category=category, value=combo.itemData(i))
        )
        combo.blockSignals(False)

    @Slot()
    def discard_settings(self) -> None:
        for category, combo in self._row_options.combo.items():
            combo.setCurrentIndex(combo.findData(self.vm.get_current_value(category)))

    def set_enabled(self, state: bool) -> None:
        for combo in self._row_options.combo.values():
            combo.setEnabled(state)
            combo.setToolTip(
                _("Please wait… Transcription in progress") if not state else ""
            )
        for reset_btn in self._row_options.reset_btn.values():
            reset_btn.setEnabled(state)
            reset_btn.setToolTip(
                _("Please wait… Transcription in progress") if not state else ""
            )
