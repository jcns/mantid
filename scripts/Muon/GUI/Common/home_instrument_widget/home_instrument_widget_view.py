# Mantid Repository : https://github.com/mantidproject/mantid
#
# Copyright &copy; 2018 ISIS Rutherford Appleton Laboratory UKRI,
#     NScD Oak Ridge National Laboratory, European Spallation Source
#     & Institut Laue - Langevin
# SPDX - License - Identifier: GPL - 3.0 +
# -*- coding: utf8 -*-

from __future__ import (absolute_import, division, print_function)

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal as Signal
from Muon.GUI.Common.utilities.muon_file_utils import allowed_instruments
from Muon.GUI.Common.utilities.run_string_utils import valid_float_regex
from Muon.GUI.Common.message_box import warning


class InstrumentWidgetView(QtGui.QWidget):
    dataChanged = Signal()

    def __init__(self, parent=None):
        super(InstrumentWidgetView, self).__init__(parent)

        self.layout = QtGui.QGridLayout(self)

        self._button_height = 40
        self._cached_instrument = ["None", "None"]

        self.setup_interface()
        self.dead_time_file_loader_hidden(True)
        self.dead_time_other_file_hidden(True)

        self.deadtime_selector.currentIndexChanged.connect(self.on_dead_time_combo_changed)
        self.rebin_selector.currentIndexChanged.connect(self.on_rebin_combo_changed)
        self.timezero_checkbox.stateChanged.connect(self.on_time_zero_checkbox_state_change)
        self.firstgooddata_checkbox.stateChanged.connect(self.on_first_good_data_checkbox_state_change)

        self._on_dead_time_from_data_selected = None
        self._on_dead_time_from_other_file_selected = lambda: 0

        self.firstgooddata_checkbox.setChecked(True)
        self.timezero_checkbox.setChecked(True)
        self.time_zero_edit_enabled(True)
        self.first_good_data_edit_enabled(True)

        self._on_time_zero_changed = lambda: 0
        self._on_first_good_data_changed = lambda: 0
        self._on_dead_time_from_file_selected = lambda: 0
        self._on_dead_time_file_option_selected = lambda: 0
        self._on_dead_time_unselected = lambda: 0

        self.timezero_edit.editingFinished.connect(
            lambda: self._on_time_zero_changed() if not self.is_time_zero_checked() else None)
        self.firstgooddata_edit.editingFinished.connect(
            lambda: self._on_first_good_data_changed() if not self.is_first_good_data_checked() else None)
        self.deadtime_file_selector.currentIndexChanged.connect(self.on_dead_time_file_combo_changed)

    def setup_interface(self):
        self.setObjectName("InstrumentWidget")

        self.setup_instrument_row()
        self.setup_time_zero_row()
        self.setup_first_good_data_row()
        self.setup_dead_time_row()
        self.setup_rebin_row()

        self.group = QtGui.QGroupBox("Instrument")
        self.group.setFlat(False)
        self.setStyleSheet("QGroupBox {border: 1px solid grey;border-radius: 10px;margin-top: 1ex; margin-right: 0ex}"
                           "QGroupBox:title {"
                           'subcontrol-origin: margin;'
                           "padding: 0 3px;"
                           'subcontrol-position: top center;'
                           'padding-top: 0px;'
                           'padding-bottom: 0px;'
                           "padding-right: 10px;"
                           ' color: grey; }')

        self.group.setLayout(self.layout)

        self.group2 = QtGui.QGroupBox("Rebin")
        self.group2.setFlat(False)

        self.group2.setLayout(self.horizontal_layout_5)

        self.widget_layout = QtGui.QVBoxLayout(self)
        self.widget_layout.addWidget(self.group)
        self.widget_layout.addWidget(self.group2)
        self.setLayout(self.widget_layout)

    def show_file_browser_and_return_selection(self, file_filter, search_directories, multiple_files=False):
        default_directory = search_directories[0]
        if multiple_files:
            chosen_files = QtGui.QFileDialog.getOpenFileNames(self, "Select files", default_directory,
                                                              file_filter)
            return [str(chosen_file) for chosen_file in chosen_files]
        else:
            chosen_file = QtGui.QFileDialog.getOpenFileName(self, "Select file", default_directory,
                                                            file_filter)
            return [str(chosen_file)]

    def set_combo_boxes_to_default(self):
        self.rebin_selector.setCurrentIndex(0)
        self.rebin_fixed_hidden(True)
        self.rebin_variable_hidden(True)
        self.deadtime_selector.setCurrentIndex(0)
        self.dead_time_data_info_hidden(True)
        self.dead_time_file_loader_hidden(True)

    def set_checkboxes_to_defualt(self):
        self.timezero_checkbox.setChecked(True)
        self.firstgooddata_checkbox.setChecked(True)

    def warning_popup(self, message):
        warning(message, parent=self)

    # ------------------------------------------------------------------------------------------------------------------
    # Instrument selection
    # ------------------------------------------------------------------------------------------------------------------

    def _fixed_aspect_ratio_size_policy(self, widget):
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        return size_policy

    def setup_instrument_row(self):
        self.instrument_selector = QtGui.QComboBox(self)
        self.instrument_selector.setSizePolicy(self._fixed_aspect_ratio_size_policy(self.instrument_selector))
        self.instrument_selector.setObjectName("instrumentSelector")
        self.instrument_selector.addItems(["None"] + allowed_instruments)

        self.instrument_label = QtGui.QLabel(self)
        self.instrument_label.setObjectName("instrumentLabel")
        self.instrument_label.setText("Instrument : ")

        self.horizontal_layout = QtGui.QHBoxLayout()
        self.horizontal_layout.setObjectName("horizontalLayout")
        self.horizontal_layout.addWidget(self.instrument_label)
        self.horizontal_layout.addWidget(self.instrument_selector)
        self.horizontal_layout.addStretch(0)

        self.layout.addWidget(self.instrument_label, 0, 0)
        self.layout.addWidget(self.instrument_selector, 0, 1)

    def get_instrument(self):
        return str(self.instrument_selector.currentText())

    def set_instrument(self, instrument, block=False):
        index = self.instrument_selector.findText(instrument)
        if index != -1:
            self.instrument_selector.blockSignals(block)
            self.instrument_selector.setCurrentIndex(index)
            self.instrument_selector.blockSignals(False)

    def on_instrument_changed(self, slot):
        self.instrument_selector.currentIndexChanged.connect(slot)
        self.instrument_selector.currentIndexChanged.connect(self.cache_instrument)

    def cache_instrument(self):
        self._cached_instrument.pop(0)
        self._cached_instrument.append(str(self.instrument_selector.currentText()))

    @property
    def cached_instrument(self):
        return self._cached_instrument[-1]

    def instrument_changed_warning(self):
        msg = QtGui.QMessageBox(self)
        msg.setIcon(QtGui.QMessageBox.Warning)
        msg.setText("Changing instrument will reset the interface, continue?")
        msg.setWindowTitle("Changing Instrument")
        msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        retval = msg.exec_()
        if retval == 1024:
            # The "OK" code
            return 1
        else:
            return 0

    # ------------------------------------------------------------------------------------------------------------------
    # Time zero
    # ------------------------------------------------------------------------------------------------------------------

    def setup_time_zero_row(self):
        self.timezero_label = QtGui.QLabel(self)
        self.timezero_label.setObjectName("timeZeroLabel")
        self.timezero_label.setText("Time Zero : ")

        self.timezero_edit = QtGui.QLineEdit(self)
        timezero_validator = QtGui.QRegExpValidator(QtCore.QRegExp(valid_float_regex), self.timezero_edit)
        self.timezero_edit.setValidator(timezero_validator)
        self.timezero_edit.setObjectName("timeZeroEdit")
        self.timezero_edit.setText("")

        self.timezero_unit_label = QtGui.QLabel(self)
        self.timezero_unit_label.setObjectName("timeZeroUnitLabel")
        self.timezero_unit_label.setText(u"\u03BCs (From data file ")

        self.timezero_checkbox = QtGui.QCheckBox(self)
        self.timezero_checkbox.setObjectName("timeZeroCheckbox")
        self.timezero_checkbox.setChecked(True)

        self.timezero_label_2 = QtGui.QLabel(self)
        self.timezero_label_2.setObjectName("timeZeroLabel")
        self.timezero_label_2.setText(" )")

        self.horizontal_layout_2 = QtGui.QHBoxLayout()
        self.horizontal_layout_2.setObjectName("horizontalLayout2")
        self.horizontal_layout_2.addSpacing(10)
        self.horizontal_layout_2.addWidget(self.timezero_unit_label)
        self.horizontal_layout_2.addWidget(self.timezero_checkbox)
        self.horizontal_layout_2.addWidget(self.timezero_label_2)
        self.horizontal_layout_2.addStretch(0)

        self.layout.addWidget(self.timezero_label, 1, 0)
        self.layout.addWidget(self.timezero_edit, 1, 1)
        self.layout.addItem(self.horizontal_layout_2, 1, 2)

    def set_time_zero(self, time_zero):
        self.timezero_edit.setText("{0:.3f}".format(round(float(time_zero), 3)))

    def get_time_zero(self):
        return float(self.timezero_edit.text())

    def time_zero_edit_enabled(self, enabled):
        self.timezero_edit.setEnabled(not enabled)

    def is_time_zero_checked(self):
        return self.timezero_checkbox.isChecked()

    def on_time_zero_changed(self, slot):
        self._on_time_zero_changed = slot

    def on_time_zero_checkState_changed(self, slot):
        self.timezero_checkbox.stateChanged.connect(slot)

    def time_zero_state(self):
        return self.timezero_checkbox.isChecked()

    def on_time_zero_checkbox_state_change(self):
        self.time_zero_edit_enabled(self.timezero_checkbox.isChecked())

    # ------------------------------------------------------------------------------------------------------------------
    # First good data
    # ------------------------------------------------------------------------------------------------------------------

    def setup_first_good_data_row(self):

        self.firstgooddata_label = QtGui.QLabel(self)
        self.firstgooddata_label.setObjectName("firstgooddataLabel")
        self.firstgooddata_label.setText("First Good Data : ")

        self.firstgooddata_edit = QtGui.QLineEdit(self)
        firstgooddata_validator = QtGui.QRegExpValidator(QtCore.QRegExp(valid_float_regex), self.timezero_edit)
        self.timezero_edit.setValidator(firstgooddata_validator)
        self.firstgooddata_edit.setObjectName("firstgooddataEdit")
        self.firstgooddata_edit.setText("")

        self.firstgooddata_unit_label = QtGui.QLabel(self)
        self.firstgooddata_unit_label.setObjectName("firstgooddataUnitLabel")
        self.firstgooddata_unit_label.setText(u" \u03BCs (From data file ")

        self.firstgooddata_checkbox = QtGui.QCheckBox(self)
        self.firstgooddata_checkbox.setObjectName("firstgooddataCheckbox")
        self.firstgooddata_checkbox.setChecked(True)

        self.firstgooddata_label_2 = QtGui.QLabel(self)
        self.firstgooddata_label_2.setObjectName("timeZeroLabel")
        self.firstgooddata_label_2.setText(" )")

        self.horizontal_layout_3 = QtGui.QHBoxLayout()
        self.horizontal_layout_3.setObjectName("horizontalLayout3")
        self.horizontal_layout_3.addSpacing(10)
        self.horizontal_layout_3.addWidget(self.firstgooddata_unit_label)
        self.horizontal_layout_3.addWidget(self.firstgooddata_checkbox)
        self.horizontal_layout_3.addWidget(self.firstgooddata_label_2)
        self.horizontal_layout_3.addStretch(0)

        self.layout.addWidget(self.firstgooddata_label, 2, 0)
        self.layout.addWidget(self.firstgooddata_edit, 2, 1)
        self.layout.addItem(self.horizontal_layout_3, 2, 2)

    def on_first_good_data_changed(self, slot):
        self._on_first_good_data_changed = slot

    def set_first_good_data(self, first_good_data):
        self.firstgooddata_edit.setText("{0:.3f}".format(round(float(first_good_data), 3)))

    def on_first_good_data_checkState_changed(self, slot):
        self.firstgooddata_checkbox.stateChanged.connect(slot)

    def first_good_data_state(self):
        return self.firstgooddata_checkbox.checkState()

    def is_first_good_data_checked(self):
        return self.firstgooddata_checkbox.checkState()

    def on_first_good_data_checkbox_state_change(self):
        self.first_good_data_edit_enabled(self.firstgooddata_checkbox.checkState())

    def first_good_data_edit_enabled(self, disabled):
        self.firstgooddata_edit.setEnabled(not disabled)

    def get_first_good_data(self):
        return float(self.firstgooddata_edit.text())

    # ------------------------------------------------------------------------------------------------------------------
    # Dead time correction
    # ------------------------------------------------------------------------------------------------------------------

    def setup_dead_time_row(self):
        self.deadtime_label = QtGui.QLabel(self)
        self.deadtime_label.setObjectName("deadTimeLabel")
        self.deadtime_label.setText("Dead Time : ")

        self.deadtime_selector = QtGui.QComboBox(self)
        self.deadtime_selector.setObjectName("deadTimeSelector")
        self.deadtime_selector.addItems(["None", "From data file", "From table workspace", "From other file"])

        self.deadtime_label_2 = QtGui.QLabel(self)
        self.deadtime_label_2.setObjectName("deadTimeFileLabel")
        self.deadtime_label_2.setText("Dead Time Workspace : ")

        self.deadtime_label_3 = QtGui.QLabel(self)
        self.deadtime_label_3.setObjectName("deadTimeInfoLabel")
        self.deadtime_label_3.setText("")

        self.deadtime_file_selector = QtGui.QComboBox(self)
        self.deadtime_file_selector.setObjectName("deadTimeCombo")
        self.deadtime_file_selector.addItem("None")
        self.deadtime_file_selector.setToolTip("Select a table which is loaded into the ADS.")

        self.deadtime_browse_button = QtGui.QPushButton(self)
        self.deadtime_browse_button.setObjectName("deadTimeBrowseButton")
        self.deadtime_browse_button.setText("Browse")
        self.deadtime_browse_button.setToolTip("Browse for a .nxs file to load dead times from. If valid, the "
                                               "dead times will be saved as a table, and automatically selected "
                                               "as the dead time for the current data.")

        self.horizontal_layout_4 = QtGui.QHBoxLayout()
        self.horizontal_layout_4.setObjectName("horizontalLayout3")
        self.horizontal_layout_4.addSpacing(10)
        self.horizontal_layout_4.addWidget(self.deadtime_label_3)

        self.dead_time_file_layout = QtGui.QHBoxLayout()
        self.dead_time_file_layout.addWidget(self.deadtime_browse_button)
        self.dead_time_file_layout.addStretch(0)

        self.dead_time_other_file_label = QtGui.QLabel(self)
        self.dead_time_other_file_label.setText("From other file : ")

        self.layout.addWidget(self.deadtime_label, 3, 0)
        self.layout.addWidget(self.deadtime_selector, 3, 1)
        self.layout.addItem(self.horizontal_layout_4, 3, 2)
        self.layout.addWidget(self.deadtime_label_2, 4, 0)
        self.layout.addWidget(self.deadtime_file_selector, 4, 1)
        self.layout.addWidget(self.dead_time_other_file_label, 5, 0)
        self.layout.addWidget(self.deadtime_browse_button, 5, 1)

    def on_dead_time_file_option_changed(self, slot):
        self._on_dead_time_file_option_selected = slot

    def on_dead_time_from_data_selected(self, slot):
        self._on_dead_time_from_data_selected = slot

    def on_dead_time_unselected(self, slot):
        self._on_dead_time_unselected = slot

    def on_dead_time_browse_clicked(self, slot):
        self.deadtime_browse_button.clicked.connect(slot)

    def on_dead_time_from_file_selected(self, slot):
        self._on_dead_time_from_file_selected = slot

    def populate_dead_time_combo(self, names):
        self.deadtime_file_selector.blockSignals(True)
        self.deadtime_file_selector.clear()
        self.deadtime_file_selector.addItem("None")
        for name in names:
            self.deadtime_file_selector.addItem(name)
        self.deadtime_file_selector.blockSignals(False)

    def get_dead_time_file_selection(self):
        return self.deadtime_file_selector.currentText()

    def set_dead_time_file_selection_text(self, text):
        index = self.deadtime_file_selector.findText(text)
        if index >= 0:
            self.deadtime_file_selector.setCurrentIndex(index)
            return True
        return False

    def set_dead_time_file_selection(self, index):
        self.deadtime_file_selector.setCurrentIndex(index)

    def set_dead_time_selection(self, index):
        self.deadtime_selector.setCurrentIndex(index)

    def dead_time_file_loader_hidden(self, hidden=True):
        if hidden:
            self.deadtime_file_selector.hide()

            self.deadtime_label_2.hide()
            self.dead_time_data_info_hidden(hidden)
        if not hidden:
            self.deadtime_file_selector.setVisible(True)
            self.deadtime_label_2.setVisible(True)
            self.dead_time_data_info_hidden(hidden)

    def dead_time_other_file_hidden(self, hidden):
        if hidden:
            self.dead_time_other_file_label.hide()
            self.deadtime_browse_button.hide()

        if not hidden:
            self.deadtime_browse_button.setVisible(True)
            self.dead_time_other_file_label.setVisible(True)

    def dead_time_data_info_hidden(self, hidden=True):
        if hidden:
            self.deadtime_label_3.hide()
        if not hidden:
            self.deadtime_label_3.setVisible(True)

    def set_dead_time_label(self, text):
        self.deadtime_label_3.setText(text)

    def on_dead_time_combo_changed(self, index):
        if index == 0:
            self._on_dead_time_unselected()
            self.dead_time_file_loader_hidden(True)
            self.dead_time_data_info_hidden(True)
            self.dead_time_other_file_hidden(True)
        if index == 1:
            self._on_dead_time_from_data_selected()
            self.dead_time_file_loader_hidden(True)
            self.dead_time_data_info_hidden(False)
            self.dead_time_other_file_hidden(True)
        if index == 2:
            self._on_dead_time_from_file_selected()
            self.dead_time_file_loader_hidden(False)
            self.dead_time_data_info_hidden(False)
            self.dead_time_other_file_hidden(True)
        if index == 3:
            self._on_dead_time_from_other_file_selected()
            self.dead_time_file_loader_hidden(True)
            self.dead_time_data_info_hidden(True)
            self.dead_time_other_file_hidden(False)

    def on_dead_time_from_other_file_selected(self, slot):
        self._on_dead_time_from_other_file_selected = slot

    def on_dead_time_file_combo_changed(self, index):
        self._on_dead_time_file_option_selected()

    # ------------------------------------------------------------------------------------------------------------------
    # Rebin row
    # ------------------------------------------------------------------------------------------------------------------

    def setup_rebin_row(self):
        self.rebin_label = QtGui.QLabel(self)
        self.rebin_label.setObjectName("rebinLabel")
        self.rebin_label.setText("Rebin : ")

        self.rebin_selector = QtGui.QComboBox(self)
        self.rebin_selector.setObjectName("rebinSelector")
        self.rebin_selector.addItems(["None", "Fixed", "Variable"])

        self.rebin_steps_label = QtGui.QLabel(self)
        self.rebin_steps_label.setText("Steps : ")

        self.rebin_steps_edit = QtGui.QLineEdit(self)
        int_validator = QtGui.QDoubleValidator()
        self.rebin_steps_edit.setValidator(int_validator)
        self.rebin_steps_edit.setToolTip('Value to scale current bin width by.')

        self.rebin_variable_label = QtGui.QLabel(self)
        self.rebin_variable_label.setText("Bin Boundaries : ")
        self.rebin_variable_edit = QtGui.QLineEdit(self)
        self.rebin_variable_edit.setToolTip('A comma separated list of first bin boundary, width, last bin boundary.\n'
                                            'Optionally this can be followed by a comma and more widths and last boundary pairs.\n'
                                            'Optionally this can also be a single number, which is the bin width.\n'
                                            'Negative width values indicate logarithmic binning.\n\n'
                                            'For example:\n'
                                            '2,-0.035,10: from 2 rebin in Logarithmic bins of 0.035 up to 10;\n'
                                            '0,100,10000,200,20000: from 0 rebin in steps of 100 to 10,000 then steps of 200 to 20,000')
        variable_validator = QtGui.QRegExpValidator(QtCore.QRegExp('^(\s*-?\d+(\.\d+)?)(\s*,\s*-?\d+(\.\d+)?)*$'))
        self.rebin_variable_edit.setValidator(variable_validator)

        self.horizontal_layout_5 = QtGui.QHBoxLayout()
        self.horizontal_layout_5.setObjectName("horizontalLayout3")
        self.horizontal_layout_5.addSpacing(10)

        self.horizontal_layout_5.addWidget(self.rebin_label)
        self.horizontal_layout_5.addWidget(self.rebin_selector)

        self.horizontal_layout_5.addWidget(self.rebin_steps_label)
        self.horizontal_layout_5.addWidget(self.rebin_steps_edit)
        self.horizontal_layout_5.addWidget(self.rebin_variable_label)
        self.horizontal_layout_5.addWidget(self.rebin_variable_edit)
        self.horizontal_layout_5.addStretch(0)
        self.horizontal_layout_5.addSpacing(10)

        self.rebin_steps_label.hide()
        self.rebin_steps_edit.hide()
        self.rebin_variable_label.hide()
        self.rebin_variable_edit.hide()

    def rebin_fixed_hidden(self, hidden=True):
        if hidden:
            self.rebin_steps_label.hide()
            self.rebin_steps_edit.hide()
        if not hidden:
            self.rebin_steps_label.setVisible(True)
            self.rebin_steps_edit.setVisible(True)

    def rebin_variable_hidden(self, hidden=True):
        if hidden:
            self.rebin_variable_label.hide()
            self.rebin_variable_edit.hide()
        if not hidden:
            self.rebin_variable_label.setVisible(True)
            self.rebin_variable_edit.setVisible(True)

    def on_rebin_combo_changed(self, index):
        if index == 0:
            self.rebin_fixed_hidden(True)
            self.rebin_variable_hidden(True)
        if index == 1:
            self.rebin_fixed_hidden(False)
            self.rebin_variable_hidden(True)
        if index == 2:
            self.rebin_fixed_hidden(True)
            self.rebin_variable_hidden(False)

    def on_fixed_rebin_edit_changed(self, slot):
        self.rebin_steps_edit.editingFinished.connect(slot)

    def on_variable_rebin_edit_changed(self, slot):
        self.rebin_variable_edit.editingFinished.connect(slot)

    def on_rebin_type_changed(self, slot):
        self.rebin_selector.currentIndexChanged.connect(slot)

    def get_fixed_bin_text(self):
        return self.rebin_steps_edit.text()

    def get_variable_bin_text(self):
        return self.rebin_variable_edit.text()
