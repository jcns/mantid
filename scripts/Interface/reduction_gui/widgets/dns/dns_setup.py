from PyQt4.QtGui import QLineEdit, QPushButton, QTableView, QHeaderView, QCheckBox, QDoubleSpinBox, QRadioButton, \
    QLayout, QWidget, QSpacerItem, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGroupBox, QGridLayout, QButtonGroup, \
    QSizePolicy, QMessageBox, QAbstractItemView
from PyQt4.QtCore import QAbstractTableModel, pyqtSignal, QModelIndex, Qt

from reduction_gui.widgets.base_widget import BaseWidget
from reduction_gui.reduction.dns.dns_reduction import DNSScriptElement


class DNSSetupWidget(BaseWidget):
    """
    Widget that presents the options for DNS-Reduction
    """

    # Widget name
    name = "DNS Reduction"

    class DataTable(QAbstractTableModel):
        """
        The list of data runs, names of the output workspaces and comments.
        """

        def __init__(self, parent):
            QAbstractTableModel.__init__(self, parent)
            self.tableData = []

        def _numRows(self):
            """
            :return: number of rows with data
            """
            return len(self.tableData)

        def _getRow(self, row):
            """
            :param row: int of the row to get 
            :return: data of the row
            """
            return self.tableData[row] if row < self._numRows() else ("", "", "")

        def _isRowEmpty(self, row):
            """
            :param row: int of the row to check
            :return: bool if row is empty
            """
            (runs, outWs, comment) = self._getRow(row)
            return not str(runs).strip() and not str(outWs).strip() and not str(comment).strip()

        def _removeTrailingEmptyRows(self):
            """
            remove all rows at the end of the table that are empty
            """
            for row in reversed(range(self._numRows())):
                if self._isRowEmpty(row):
                    del self.tableData[row]
                else:
                    break

        def _removeEmptyRows(self):
            """
            remove all empty rows 
            """
            for row in reversed(range(self._numRows())):
                if self._isRowEmpty(row):
                    del self.tableData[row]

        def _ensureHasRows(self, numRows):
            """
            ensure the table has numRows
            :param numRows:  number of rows that should exist
            """
            while self._numRows() < numRows:
                self.tableData.append(("", "", ""))

        def _setCellText(self, row, col, text):
            """
            set the text of a cell
            :param row: row of the cell
            :param col: column of the cell
            :param text: text for the cell
            """
            self._ensureHasRows(row + 1)
            (runNumbers, outWs, comment) = self.tableData[row]

            text = str(text).strip()
            if col == 0:
                runNumbers = text
            elif col == 1:
                outWs = text
            else:
                comment = text

            self.tableData[row] = (runNumbers, outWs, comment)

        def _getCellText(self, row, col):
            """
            get the text of a cell
            :param row: row of the cell
            :param col: column of the cell
            :return: text of the cell
            """
            return str(self._getRow(row)[col]).strip()

        # reimplemented QAbstractTableModel methods

        headers    = ("Run numbers", "Output Workspace", "Comment")
        selectCell = pyqtSignal(QModelIndex)

        def emptyCells(self, indexes):
            """
            empty the cells with the indexes
            :param indexes: indexes of the cells to be emptied
            """
            for index in indexes:
                row = index.row()
                col = index.column()

                self._setCellText(row, col, "")

            self._removeEmptyRows()
            self.reset()
            # indexes is never empty
            self.selectCell.emit(indexes[0])

        def rowCount(self, _=QModelIndex()):
            """
            number of rows
            :return: returns the number of rows
            """
            # one additional row for new data
            return self._numRows() + 1

        def columnCount(self, _=QModelIndex()):
            """
            number of columns
            :return: number of columns, is always 3
            """
            return 3

        def headerData(self, selection, orientation, role):
            """
            header of the selection
            :param selection: selected cells
            :param orientation: orientation of selection
            :param role: role of the selection
            :return: header of the selection
            """
            if Qt.Horizontal == orientation and Qt.DisplayRole == role:
                return self.headers[selection]
            return None

        def data(self, index, role):
            """
            data of the cell
            :param index: index of the cell
            :param role: role of the cell
            :return: data of the cell
            """
            if Qt.DisplayRole == role or Qt.EditRole == role:
                return self._getCellText(index.row(), index.column())
            return None

        def setData(self, index, text, _):
            """
            set text in the cell
            :param index: index of the cell
            :param text: text for the cell
            :return: true if data is set
            """
            row = index.row()
            col = index.column()

            self._setCellText(row, col, text)
            self._removeTrailingEmptyRows()

            self.reset()

            # move selection to the next column or row
            col = col + 1

            if col >= 3:
                row = row + 1
                col = 0

            row = min(row, self.rowCount() - 1)
            self.selectCell.emit(self.index(row, col))

            return True

        def flags(self, _):
            """
            flags for the table
            :return: flags
            """
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    class MaskDetTable(QAbstractTableModel):

        def __init__(self, parent):
            QAbstractTableModel.__init__(self, parent)
            self.tableData = []

        def _numRows(self):
            """
            :return: number of rows with data
            """
            return len(self.tableData)

        def _getRow(self, row):
            """
            :param row: int of the row to get
            :return: data of the row
            """
            return self.tableData[row] if row < self._numRows() else ("", "")

        def _isRowEmpty(self, row):
            """
            checks if the row is empty
            :param row: int of the row to check
            :return: true if row is empty
            """
            (minAngle, maxAngle) = self._getRow(row)
            return not str(minAngle).strip() and not str(maxAngle).strip()

        def _removeTrailingEmptyRows(self):
            """
            removes all empty rows at the end of the table
            """
            for row in reversed(range(self._numRows())):
                if self._isRowEmpty(row):
                    del self.tableData[row]
                else:
                    break

        def _removeEmptyRows(self):
            """
            removes all empty rows
            """
            for row in reversed(range(self._numRows())):
                if self._isRowEmpty(row):
                    del self.tableData[row]

        def _ensureHasRows(self, numRows):
            """
            ensures that there a numRows
            :param numRows: number of rows that should exist
            """
            while self._numRows() < numRows:
                self.tableData.append(("", ""))

        def _noMinAngle(self, row):
            """
            checks if there is a min angle in this row
            :param row: int of the row to be checked
            :return: true if there is no min angle
            """
            if not self._isRowEmpty(row):
                (minAngle, maxAngle) = self.tableData[row]
                return not minAngle

        def _noMaxAngle(self, row):
            """
            checks if there is a max angle in this row
            :param row: int of the row to be checked
            :return: true if there is no max angle
            """
            if not self._isRowEmpty(row):
                (minAngle, maxAngle) = self.tableData[row]
                return not maxAngle

        def _setCellText(self, row, col, text):
            """
            set the text of a cell
            :param row: row of the cell
            :param col: column of the cell
            :param text: text for the cell
            """
            self._ensureHasRows(row + 1)
            (minAngle, maxAngle) = self.tableData[row]

            text = str(text).strip()

            if col == 0:
                minAngle = text
            else:
                maxAngle = text

            self.tableData[row] = (minAngle, maxAngle)

        def _getCellText(self, row, col):
            return str(self._getRow(row)[col]).strip()

        # reimplemented QAbstractTableModel methods

        headers    = ("Min Angle[\305]", "Max Angle[\305]")
        selectCell = pyqtSignal(QModelIndex)

        def emptyCells(self, indexes):
            """
            empty the cells with the indexes
            :param indexes: indexes of the cells to be emptied
            """
            for index in indexes:
                row = index.row()
                col = index.column()

                self._setCellText(row, col, "")

            self._removeEmptyRows()
            self.reset()
            # indexes is never empty
            self.selectCell.emit(indexes[0])

        def rowNoMinAngle(self):
            """
            first row with no min angle
            :return: row with no min angle, if all rows have min angle returns none
            """
            for i in range(len(self.tableData)):
                if self._noMinAngle(i):
                    return i
            return None

        def rowNoMaxAngle(self):
            """
            first row with no max angle
            :return: row with no max angle, if all rows have max angle returns none
            """
            for i in range(len(self.tableData)):
                if self._noMaxAngle(i):
                    return i
            return None

        def rowCount(self, _=QModelIndex()):
            """
            number of rows
            :return: returns the number of rows
            """
            # one additional row for new data
            return self._numRows() + 1

        def columnCount(self, _=QModelIndex()):
            """
            number of columns
            :return: number of columns, is always 2
            """
            return 2

        def headerData(self, selction, orientation, role):
            """
            header of the selection
            :param selection: selected cells
            :param orientation: orientation of selection
            :param role: role of the selection
            :return: header of the selection
            """
            if Qt.Horizontal == orientation and Qt.DisplayRole == role:
                return self.headers[selction]
            return None

        def data(self, index, role):
            """
            data of the cell
            :param index: index of the cell
            :param role: role of the cell
            :return: data of the cell
            """
            if Qt.DisplayRole == role or Qt.EditRole == role:
                return self._getCellText(index.row(), index.column())
            return None

        def setData(self, index, text, _):
            """
            set text in the cell
            :param index: index of the cell
            :param text: text for the cell
            :return: true if data is set
            """
            row = index.row()
            col = index.column()

            self._setCellText(row, col, text)
            self._removeTrailingEmptyRows()

            self.reset()

            col = col + 1

            if col >= 2:
                row = row + 1
                col = 0

            row = min(row, self.rowCount() - 1)
            self.selectCell.emit(self.index(row, col))

            return True

        def flags(self, _):
            """
            flags for the table
            :return: flags
            """
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    class TableViews(QTableView):
        """
        View of the tables
        """

        def keyPressEvent(self, QKeyEvent):
            """
            reimplemented keyPressEvent for deleting cells and arrows in editing cells 
            :param QKeyEvent: 
            :return: 
            """
            if self.state() == QAbstractItemView.EditingState:
                index = self.currentIndex()
                if QKeyEvent.key() in [Qt.Key_Down, Qt.Key_Up]:
                    self.setFocus()
                    self.setCurrentIndex(self.model().index(index.row(), index.column()))
                else:
                    QTableView.keyPressEvent(self, QKeyEvent)
            if QKeyEvent.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
                self.model().emptyCells(self.selectedIndexes())
            else:
                QTableView.keyPressEvent(self, QKeyEvent)

    # Tips for the user how to fill in the data

    TIP_sampleDataPath    = ""
    TIP_btnSampleDataPath = ""
    TIP_sampleFilePre     = ""
    TIP_sampleFileSuff    = ""
    TIP_runsView          = ""

    TIP_maskAngle = ""

    TIP_chkSaveToFile = ""
    TIP_outDir        = ""
    TIP_btnOutDir     = ""
    TIP_outFile       = ""

    TIP_standardDataPath    = ""
    TIP_btnStandardDataPath = ""

    TIP_chkDetEffi     = ""
    TIP_chkSumVan      = ""
    TIP_chkSubInst     = ""
    TIP_subFac         = ""
    TIP_chkFlippRatio  = ""
    TIP_flippFac       = ""
    TIP_multiSF        = ""
    TIP_rbnNormTime    = ""
    TIP_rbnNormMonitor = ""
    TIP_neutronWaveLen = ""

    TIP_rbnPolyAmor = ""

    TIP_chkAxQ      = ""
    TIP_chkAxD      = ""
    TIP_chkAx2Theta = ""
    TIP_rbnXYZ      = ""
    TIP_rbnCoherent = ""
    TIP_rbnNo       = ""

    TIP_rbnSingleCryst = ""

    TIP_omegaOffset  = ""
    TIP_latticeA     = ""
    TIP_latticeB     = ""
    TIP_latticeC     = ""
    TIP_latticeAlpha = ""
    TIP_latticeBeta  = ""
    TIP_latticeGamma = ""
    TIP_scatterU1    = ""
    TIP_scatterU2    = ""
    TIP_scatterU3    = ""
    TIP_scatterV1    = ""
    TIP_scatterV2    = ""
    TIP_scatterV3    = ""

    def __init__(self, settings):

        BaseWidget.__init__(self, settings=settings)
        inf = float("inf")

        def tip(widget, text):
            """
            set tip for a widget
            :param widget: widget where the tip should be set
            :param text: text of the tip
            :return: widget
            """
            if text:
                widget.setToolTip(text)
            return widget

        def set_spin(spin, minVal=-inf, maxVal=+inf, decimals= 2):
            """
            set boundaries for spin box 
            :param spin: spin box
            :param minVal: min value of the spin box
            :param maxVal: max value of the spin box
            """
            spin.setRange(minVal, maxVal)
            spin.setDecimals(decimals)
            spin.setSingleStep(0.01)

        # ui data elements

        # sample data
        self.sampleDataPath    = tip(QLineEdit(),           self.TIP_sampleDataPath)
        self.btnSampleDataPath = tip(QPushButton("Browse"), self.TIP_btnSampleDataPath)
        self.sampleFilePre     = tip(QLineEdit(),           self.TIP_sampleFilePre)
        self.sampleFileSuff    = tip(QLineEdit(),           self.TIP_sampleFileSuff)
        self.runsView          = tip(self.TableViews(self), self.TIP_runsView)
        self.runNumbersModel   = DNSSetupWidget.DataTable(self)

        self.runsView.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.runsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.runsView.setModel(self.runNumbersModel)

        # mask detectors
        self.maskAngleView  = tip(self.TableViews(self), self.TIP_maskAngle)
        self.maskAngleModel = DNSSetupWidget.MaskDetTable(self)

        self.maskAngleView.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.maskAngleView.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.maskAngleView.setModel(self.maskAngleModel)

        # save to file
        self.chkSaveToFile = tip(QCheckBox("Save to file"), self.TIP_chkSaveToFile)
        self.outDir        = tip(QLineEdit(),               self.TIP_outDir)
        self.btnOutDir     = tip(QPushButton("Browse"),     self.TIP_btnOutDir)
        self.outFile       = tip(QLineEdit(),               self.TIP_outFile)

        # standard data
        self.standardDataPath    = tip(QLineEdit(),           self.TIP_standardDataPath)
        self.btnStandardDataPath = tip(QPushButton("Browse"), self.TIP_btnStandardDataPath)

        # data reduction settings
        self.chkdetEffi        = tip(QCheckBox("Detector efficiency correction"),            self.TIP_chkDetEffi)
        self.chksumVan         = tip(QCheckBox("Sum Vanadium over detector position"),       self.TIP_chkSumVan)
        self.chksubInst        = tip(QCheckBox("Subtract instrument background for sample"), self.TIP_chkSubInst)
        self.subFac            = tip(QDoubleSpinBox(),                                       self.TIP_subFac)
        self.chkFlippRatio     = tip(QCheckBox("Flipping ratio correction"),                 self.TIP_chkFlippRatio)
        self.flippFac          = tip(QDoubleSpinBox(),                                       self.TIP_flippFac)
        self.multiSF           = tip(QDoubleSpinBox(),                                       self.TIP_multiSF)
        self.rbnNormTime       = tip(QRadioButton("time"),                                   self.TIP_rbnNormTime)
        self.rbnNormMonitor    = tip(QRadioButton("monitor"),                                self.TIP_rbnNormMonitor)
        self.neutronWaveLength = tip(QDoubleSpinBox(),                                       self.TIP_neutronWaveLen)

        set_spin(self.subFac,            0.0)
        set_spin(self.flippFac,          0.0)
        set_spin(self.multiSF,           0.0, 1.0)
        set_spin(self.neutronWaveLength, 0.0)

        # sample type polycrystal/amorph
        self.rbnPolyAmor = tip(QRadioButton("Polycrystal/Amorphous"), self.TIP_rbnPolyAmor)
        self.chkAxQ      = tip(QCheckBox("q"),                        self.TIP_chkAxQ)
        self.chkAxD      = tip(QCheckBox("d"),                        self.TIP_chkAxD)
        self.chkAx2Theta = tip(QCheckBox(u"2\u0398"),                 self.TIP_chkAx2Theta)
        self.rbnXYZ      = tip(QRadioButton("XYZ"),                   self.TIP_rbnXYZ)
        self.rbnCoherent = tip(QRadioButton("Coherent/Incoherent"),   self.TIP_rbnCoherent)
        self.rbnNo       = tip(QRadioButton("No"),                    self.TIP_rbnNo)

        # sample type singlecrystal
        self.rbnSingleCryst = tip(QRadioButton("Single Crystal"), self.TIP_rbnSingleCryst)
        self.omegaOffset    = tip(QDoubleSpinBox(),               self.TIP_omegaOffset)
        self.latticeA       = tip(QDoubleSpinBox(),               self.TIP_latticeA)
        self.latticeB       = tip(QDoubleSpinBox(),               self.TIP_latticeB)
        self.latticeC       = tip(QDoubleSpinBox(),               self.TIP_latticeC)
        self.latticeAlpha   = tip(QDoubleSpinBox(),               self.TIP_latticeAlpha)
        self.latticeBeta    = tip(QDoubleSpinBox(),               self.TIP_latticeBeta)
        self.latticeGamma   = tip(QDoubleSpinBox(),               self.TIP_latticeGamma)
        self.scatterU1      = tip(QDoubleSpinBox(),               self.TIP_scatterU1)
        self.scatterU2      = tip(QDoubleSpinBox(),               self.TIP_scatterU2)
        self.scatterU3      = tip(QDoubleSpinBox(),               self.TIP_scatterU3)
        self.scatterV1      = tip(QDoubleSpinBox(),               self.TIP_scatterV1)
        self.scatterV2      = tip(QDoubleSpinBox(),               self.TIP_scatterV2)
        self.scatterV3      = tip(QDoubleSpinBox(),               self.TIP_scatterV3)

        set_spin(self.omegaOffset)

        set_spin(self.latticeA, 0, decimals=4)
        set_spin(self.latticeB, 0, decimals=4)
        set_spin(self.latticeC, 0, decimals=4)

        self.latticeAlpha.setMinimumWidth(75)
        self.latticeBeta.setMinimumWidth(75)
        self.latticeGamma.setMinimumWidth(75)

        set_spin(self.latticeAlpha, 5.0, 175.0)
        set_spin(self.latticeBeta,  5.0, 175.0)
        set_spin(self.latticeGamma, 5.0, 175.0)

        set_spin(self.scatterU1)
        set_spin(self.scatterU2)
        set_spin(self.scatterU3)
        set_spin(self.scatterV1)
        set_spin(self.scatterV2)
        set_spin(self.scatterV3)

        # ui layout

        def _box(cls, widgets):
            box = cls()
            for wgt in widgets:
                if isinstance(wgt, QLayout):
                    box.addLayout(wgt)
                elif isinstance(wgt, QWidget):
                    box.addWidget(wgt)
                elif isinstance(wgt, QSpacerItem):
                    box.addSpacerItem(wgt)
                else:
                    box.addStretch(wgt)
            return box

        def hbox(widgets):
            return _box(QHBoxLayout, widgets)

        def vbox(widgets):
            return _box(QVBoxLayout, widgets)

        def label(text, tip):
            label = QLabel(text)
            if tip:
                label.setToolTip(tip)
            return label

        def frame_box(frame, box) :
            frame.setFrameShape(QFrame.Box)
            frame.setLayout(box)

        # boxes to group the data

        gb_sample_data = QGroupBox("Sample data")
        gb_mask_det    = QGroupBox("Mask Detectors")
        gb_out         = QGroupBox()
        gb_std_data    = QGroupBox("Standard data")
        gb_data_red    = QGroupBox("Data reduction settings")
        gb_output      = QGroupBox()

        box = QHBoxLayout()
        self._layout.addLayout(box)

        # adding frames for every box

        sample_data_box = vbox((gb_sample_data, self.runsView))
        frame_sample_data_box = QFrame()
        frame_box(frame_sample_data_box, sample_data_box)

        mask_detectors_box = vbox((gb_mask_det,))
        frame_mask_detectors_box = QFrame()
        frame_box(frame_mask_detectors_box, mask_detectors_box)

        save_file_box = vbox((self.chkSaveToFile, gb_out))
        frame_save_file_box = QFrame()
        frame_box(frame_save_file_box, save_file_box)

        std_data_box = vbox((gb_std_data,))
        frame_std_data_box = QFrame()
        frame_box(frame_std_data_box, std_data_box)

        data_red_settings_box = vbox((gb_data_red,))
        frame_data_red_settings_box = QFrame()
        frame_box(frame_data_red_settings_box, data_red_settings_box)

        output_box = vbox((gb_output,))
        frame_output_box = QFrame()
        frame_box(frame_output_box, output_box)

        # set layout for the main widget
        box.addLayout(vbox((frame_sample_data_box, frame_mask_detectors_box, frame_save_file_box)))
        box.addLayout(vbox((frame_std_data_box, frame_data_red_settings_box, frame_output_box)))

        # set layout for sample data
        hbox_sample_data = hbox((QLabel("Data path"), self.sampleDataPath, self.btnSampleDataPath))

        grid = QGridLayout()

        grid.addLayout(hbox_sample_data,       0, 0, 1, 4)
        grid.addWidget(QLabel("File prefix"),  1, 0)
        grid.addWidget(self.sampleFilePre,     1, 1)
        grid.addWidget(QLabel("suffix"),       1, 2)
        grid.addWidget(self.sampleFileSuff,    1, 3)

        gb_sample_data.setLayout(grid)

        # set layout for mask detectors
        grid = QGridLayout()

        grid.addWidget(self.maskAngleView, 0, 0)

        gb_mask_det.setLayout(grid)

        # set layout for save to file
        grid = QGridLayout()

        grid.addWidget(QLabel("       Output directory"),   1, 0)
        grid.addWidget(self.outDir,                         1, 1)
        grid.addWidget(self.btnOutDir,                      1, 2)
        grid.addWidget(QLabel("       Output file prefix"), 2, 0)
        grid.addWidget(self.outFile,                        2, 1)

        gb_out.setLayout(grid)
        gb_out.setContentsMargins(0, 0, 0, 0)

        self.SaveLines = []
        self.SaveLines.append(self.outDir)
        self.SaveLines.append(self.outFile)

        # set layout for standard data
        grid = QGridLayout()

        grid.addWidget(QLabel("Path"),           1, 1)
        grid.addWidget(self.standardDataPath,    1, 2)
        grid.addWidget(self.btnStandardDataPath, 1, 3)

        gb_std_data.setLayout(grid)

        # set layout for data reduction settings
        grid = QGridLayout()

        spacer_fac1 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        spacer_fac2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)

        hbox_sum_van    = hbox((QLabel("      "), self.chksumVan,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_sub_inst   = hbox((QLabel("      "), QLabel("Factor"), self.subFac,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_flip       = hbox((QLabel("      "), QLabel("Factor"), self.flippFac,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_multi_sp   = hbox((QLabel("Multiple SF scattering probability"), self.multiSF,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_normalise  = hbox((QLabel("Normalization"), self.rbnNormTime, self.rbnNormMonitor,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_wavelength = hbox((QLabel("Neutron wavelength (\305)"), self.neutronWaveLength,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        bnt_group = QButtonGroup(self)
        bnt_group.addButton(self.rbnNormMonitor)
        bnt_group.addButton(self.rbnNormTime)

        grid.addWidget(self.chkdetEffi,    0, 0, 1, 2)
        grid.addLayout(hbox_sum_van,       1, 0, 1, 3)
        grid.addWidget(self.chksubInst,    2, 0, 1, 3)
        grid.addLayout(hbox_sub_inst,      3, 0, 1, 4)
        grid.addItem(spacer_fac1,          4, 0)
        grid.addWidget(self.chkFlippRatio, 5, 0, 1, 2)
        grid.addLayout(hbox_flip,          6, 0, 1, 4)
        grid.addItem(spacer_fac2,          7, 0)
        grid.addLayout(hbox_multi_sp,      8, 0, 1, 3)
        grid.addLayout(hbox_normalise,     9, 0, 1, 4)
        grid.addLayout(hbox_wavelength,   10, 0, 1, 3)

        gb_data_red.setLayout(grid)

        # set layout for sample data parameter
        grid = QGridLayout()

        spacer_rbn = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Minimum)

        hbox_ax         = hbox((self.chkAxQ, self.chkAxD,      self.chkAx2Theta))
        hbox_normalise  = hbox((self.rbnXYZ, self.rbnCoherent, self.rbnNo))

        hbox_wavelength = hbox((QLabel("Omega offset"), self.omegaOffset,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        hbox_lattice_a = hbox((QLabel("a[\305]"), self.latticeA,
                               QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_lattice_b = hbox((QLabel("b[\305]"), self.latticeB,
                               QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_lattice_c = hbox((QLabel("c[\305]"), self.latticeC,
                               QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        hbox_lattice_alpha = hbox((QLabel(u"\u03B1[\u00B0]"), self.latticeAlpha,
                                   QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_lattice_beta  = hbox((QLabel(u"\u03B2[\u00B0]"),self.latticeBeta,
                                   QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hbox_lattice_gamma = hbox((QLabel(u"\u03B3[\u00B0]"), self.latticeGamma,
                                   QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        grid_lattice = QGridLayout()

        grid_lattice.addLayout(hbox_lattice_a,     0, 0)
        grid_lattice.addLayout(hbox_lattice_b,     0, 1)
        grid_lattice.addLayout(hbox_lattice_c,     0, 2)
        grid_lattice.addLayout(hbox_lattice_alpha, 1, 0)
        grid_lattice.addLayout(hbox_lattice_beta,  1, 1)
        grid_lattice.addLayout(hbox_lattice_gamma, 1, 2)

        hbox_scatter_v = hbox((QLabel("v"), self.scatterV1, self.scatterV2, self.scatterV3))
        hbox_scatter_u = hbox((QLabel("u"), self.scatterU1, self.scatterU2, self.scatterU3, hbox_scatter_v))

        grid.addWidget(self.rbnPolyAmor,             0, 0, 1, 2)
        grid.addWidget(QLabel("Abscissa"),           1, 1)
        grid.addLayout(hbox_ax,                      2, 1, 1, 3)
        grid.addWidget(QLabel("Separation"),         3, 1)
        grid.addLayout(hbox_normalise,               4, 1)
        grid.addItem(spacer_rbn,                     5, 0)
        grid.addWidget(self.rbnSingleCryst,          6, 0, 1, 2)
        grid.addLayout(hbox_wavelength,              7, 1, 1, 2)
        grid.addWidget(QLabel("Lattice parameters"), 8, 1)
        grid.addLayout(grid_lattice,                 9, 1)
        grid.addWidget(QLabel("Scattering Plane"),  11, 1)
        grid.addLayout(hbox_scatter_u,              12, 1, 1, 4)

        gb_output.setLayout(grid)
        gb_output.setContentsMargins(0, 0, 0, 0)

        bnt_group = QButtonGroup(self)
        bnt_group.addButton(self.rbnPolyAmor)
        bnt_group.addButton(self.rbnSingleCryst)

        bnt_group = QButtonGroup(self)
        bnt_group.addButton(self.rbnXYZ)
        bnt_group.addButton(self.rbnCoherent)
        bnt_group.addButton(self.rbnNo)

        self.ChecksPolyAmor = []
        self.ChecksPolyAmor.append(self.chkAxD)
        self.ChecksPolyAmor.append(self.chkAxQ)
        self.ChecksPolyAmor.append(self.chkAx2Theta)

        self.RbnsPolyAmor = []
        self.RbnsPolyAmor.append(self.rbnXYZ)
        self.RbnsPolyAmor.append(self.rbnCoherent)
        self.RbnsPolyAmor.append(self.rbnNo)

        self.SpinsSingle = []
        self.SpinsSingle.append(self.omegaOffset)
        self.SpinsSingle.append(self.latticeA)
        self.SpinsSingle.append(self.latticeB)
        self.SpinsSingle.append(self.latticeC)
        self.SpinsSingle.append(self.latticeAlpha)
        self.SpinsSingle.append(self.latticeBeta)
        self.SpinsSingle.append(self.latticeGamma)
        self.SpinsSingle.append(self.scatterU1)
        self.SpinsSingle.append(self.scatterU2)
        self.SpinsSingle.append(self.scatterU3)
        self.SpinsSingle.append(self.scatterV1)
        self.SpinsSingle.append(self.scatterV2)
        self.SpinsSingle.append(self.scatterV3)

        # connections
        self.btnSampleDataPath.clicked.connect(self._sampleDataDir)
        self.runNumbersModel.selectCell.connect(self._onSelectedCell)
        self.maskAngleModel.selectCell.connect(self._onSelectedCellMask)
        self.chkSaveToFile.clicked.connect(self._saveFileChanged)
        self.btnOutDir.clicked.connect(self._outputDir)
        self.btnStandardDataPath.clicked.connect(self._stdDataDir)
        self.chkdetEffi.clicked.connect(self._detEffiChanged)
        self.chksubInst.clicked.connect(self._subInstChanged)
        self.chkFlippRatio.clicked.connect(self._flippRatioChanged)
        self.rbnSingleCryst.clicked.connect(self._rbnOutChanged)
        self.rbnPolyAmor.clicked.connect(self._rbnOutChanged)

    def _sampleDataDir(self):
        """
        dialog to browse for the directory with sample data
        """
        direction_name = self.dir_browse_dialog()
        if direction_name:
            self.sampleDataPath.setText(direction_name)

    def _onSelectedCell(self, index):
        """
        set focus on selected cell
        :param index: index of the cell to set focus on
        """
        self.runsView.setCurrentIndex(index)
        self.runsView.setFocus()

    def _onSelectedCellMask(self, index):
        """
        set focus on selected cell
        :param index: index of the cell to set focus on
        """
        self.maskAngleView.setCurrentIndex(index)
        self.maskAngleView.setFocus()

    def _saveFileChanged(self):
        """
        changes if the state of the save to file check box changed
        """
        if self.chkSaveToFile.isChecked():
            self._SaveFileChecked()
        else:
            self._SaveFileNotChecked()

    def _outputDir(self):
        """
        dialog to browse for the directory where the file should be saved
        """
        direction_name = self.dir_browse_dialog()
        if direction_name:
            self.outDir.setText(direction_name)

    def _stdDataDir(self):
        """
        dialog to browse for the directory with standard data
        """
        direction_name = self.dir_browse_dialog()
        if direction_name:
            self.standardDataPath.setText(direction_name)

    def _detEffiChanged(self):
        """
        changes if the state of the detector efficiency check box changed
        """
        self.chksumVan.setEnabled(False)
        # Enable sum vanadium over detector position:
        #if self.chkdetEffi.isChecked():
        #    self.chksumVan.setEnabled(True)
        #else:
        #    self.chksumVan.setEnabled(False)

    def _subInstChanged(self):
        """
        changes if the state of the subtract background check box changed
        """
        if self.chksubInst.isChecked():
            self.subFac.setEnabled(True)
        else:
            self.subFac.setEnabled(False)

    def _flippRatioChanged(self):
        """
        changes if the state of the flipping ratio check box changed
        """
        if self.chkFlippRatio.isChecked():
            self.flippFac.setEnabled(True)
        else:
            self.flippFac.setEnabled(False)

    def _rbnOutChanged(self):
        """
        changes if an different radio button of the button group for sample data type is choose
        """
        if self.rbnSingleCryst.isChecked():
            self._SingleChecked()
            self._PolyAmorNotChecked()
        elif self.rbnPolyAmor.isChecked():
            self._SingleNotChecked()
            self._PolyAmorChecked()

    def _SaveFileChecked(self):
        """
        enable lines in save to file widget
        """
        for line in self.SaveLines:
            line.setDisabled(False)
        self.btnOutDir.setEnabled(True)

    def _SaveFileNotChecked(self):
        """
        disable lines in save to file widget
        """
        for line in self.SaveLines:
            line.setDisabled(True)
        self.btnOutDir.setEnabled(False)

    def _SingleChecked(self):
        """
        enable spin boxes for single crystal parameters
        """
        for spin in self.SpinsSingle:
            spin.setEnabled(True)

    def _PolyAmorChecked(self):
        """
        enable spin boxes and check boxes for polycrystal/amporph parameters
        """
        for chkButton in self.ChecksPolyAmor:
            chkButton.setEnabled(True)
        for rbn in self.RbnsPolyAmor:
            rbn.setEnabled(True)

    def _SingleNotChecked(self):
        """
        disable spin boxes for single crystal parameters
        """
        for spin in self.SpinsSingle:
            spin.setEnabled(False)

    def _PolyAmorNotChecked(self):
        """
        disable spin boxes and check boxes for polycrystal/amporph parameters
        """
        for chkButton in self.ChecksPolyAmor:
            chkButton.setEnabled(False)
        for rbn in self.RbnsPolyAmor:
            rbn.setEnabled(False)

    def get_state(self):
        """
        get the state of the ui
        :return: script element
        """
        elem = DNSScriptElement()

        # warning for no min angle in a row
        rowNoMinAngle = self.maskAngleModel.rowNoMinAngle()
        if rowNoMinAngle is not None:
            message = "No min Angle in row: "+str(rowNoMinAngle)+" , using default: 0.0"
            QMessageBox.warning(self, "Warning", message)

        # warning for no min angle in a row
        rowNoMaxAngle = self.maskAngleModel.rowNoMaxAngle()
        if rowNoMaxAngle is not None:
            message = "No max Angle in row: "+str(rowNoMaxAngle)+" , using default: 180.0"
            QMessageBox.warning(self, "Warning", message)

        def line_text(lineEdit):
            """
            get text from line edit
            :param lineEdit: line edit widget
            :return: text of the line edit widget
            """
            return lineEdit.text().strip()

        # save facility and instrument name to element
        elem.facility_name   = self._settings.facility_name
        elem.instrument_name = self._settings.instrument_name

        # save state of sample data widget to element
        elem.sampleDataPath = line_text(self.sampleDataPath)
        elem.filePrefix     = line_text(self.sampleFilePre)
        elem.fileSuffix     = line_text(self.sampleFileSuff)
        elem.dataRuns       = self.runNumbersModel.tableData

        # save angles for mask detectors to element
        elem.maskAngles = self.maskAngleModel.tableData

        # save state of save to file widget to element
        elem.saveToFile = self.chkSaveToFile.isChecked()
        elem.outDir     = line_text(self.outDir)
        elem.outPrefix  = line_text(self.outFile)

        # save state of standard data path widget to element
        elem.standardDataPath = line_text(self.standardDataPath)

        # save state of data reduction settings widget to element
        elem.detEffi        = self.chkdetEffi.isChecked()
        elem.sumVan         = self.chksumVan.isChecked()
        elem.subInst        = self.chksubInst.isChecked()
        elem.subFac         = self.subFac.value()
        elem.flippRatio     = self.chkFlippRatio.isChecked()
        elem.flippFac       = self.flippFac.value()
        elem.multiSF        = self.multiSF.value()
        elem.neutronWaveLen = self.neutronWaveLength.value()
        elem.normalise = elem.NORM_TIME if self.rbnNormTime.isChecked() else \
            elem.NORM_MONITOR

        # save state of sample data settings to element
        elem.out = elem.OUT_POLY_AMOR if self.rbnPolyAmor.isChecked() else \
            elem.OUT_SINGLE_CRYST

        elem.outAxisQ      = self.chkAxQ.isChecked()
        elem.outAxisD      = self.chkAxD.isChecked()
        elem.outAxis2Theta = self.chkAx2Theta.isChecked()
        elem.separation    = elem.SEP_XYZ if self.rbnXYZ.isChecked() else \
            elem.SEP_COH if self.rbnCoherent.isChecked() else elem.SEP_NO

        elem.omegaOffset = self.omegaOffset.value()

        elem.latticeA     = self.latticeA.value()
        elem.latticeB     = self.latticeB.value()
        elem.latticeC     = self.latticeC.value()
        elem.latticeAlpha = self.latticeAlpha.value()
        elem.latticeBeta  = self.latticeBeta.value()
        elem.latticeGamma = self.latticeGamma.value()
        elem.scatterU1    = self.scatterU1.value()
        elem.scatterU2    = self.scatterU2.value()
        elem.scatterU3    = self.scatterU3.value()
        elem.scatterV1    = self.scatterV1.value()
        elem.scatterV2    = self.scatterV2.value()
        elem.scatterV3    = self.scatterV3.value()

        return elem

    def set_state(self, dnsScriptElement):
        """
        set state from the script element to the ui
        :param dnsScriptElement: script element
        """

        elem = dnsScriptElement

        # set state for sample data widget
        self.sampleDataPath.setText(elem.sampleDataPath)
        self.sampleFilePre.setText(elem.filePrefix)
        self.sampleFileSuff.setText(elem.fileSuffix)
        self.runNumbersModel.tableData = elem.dataRuns
        self.runNumbersModel.reset()

        # set state for mask detectors widget
        self.maskAngleModel.tableData = elem.maskAngles
        self.maskAngleModel.reset()

        # set state for save to file widget
        self.chkSaveToFile.setChecked(elem.saveToFile)
        self.outDir.setText(elem.outDir)
        self.outFile.setText(elem.outPrefix)

        if self.chkSaveToFile.isChecked():
            for line in self.SaveLines:
                line.setDisabled(False)
        else:
            for line in self.SaveLines:
                line.setDisabled(True)

        # set state for standard data widget
        self.standardDataPath.setText(elem.standardDataPath)

        # set state for data reduction settings widget
        self.chkdetEffi.setChecked(elem.detEffi)
        self.chksumVan.setChecked(elem.sumVan)
        # Disable Sum Vanadium Option
        self.chksumVan.setEnabled(False)
        # Enable Sum Vanadium Option
        #if self.chkdetEffi.isChecked():
        #    self.chksumVan.setEnabled(True)
        #else:
        #    self.chksumVan.setEnabled(False)
        self.chksubInst.setChecked(elem.subInst)
        self.subFac.setValue(elem.subFac)
        self.chkFlippRatio.setChecked(elem.flippRatio)
        self.flippFac.setValue(elem.flippFac)
        self.multiSF.setValue(elem.multiSF)
        self.multiSF.setEnabled(False)
        if elem.normalise == elem.NORM_TIME:
            self.rbnNormTime.setChecked(True)
        elif elem.normalise == elem.NORM_MONITOR:
            self.rbnNormMonitor.setChecked(True)
        self.neutronWaveLength.setValue(elem.neutronWaveLen)

        if self.chksubInst.isChecked():
            self.subFac.setEnabled(True)
        else:
            self.subFac.setEnabled(False)

        if self.chkFlippRatio.isChecked():
            self.flippFac.setEnabled(True)
        else:
            self.flippFac.setEnabled(False)

        # set state for sample data settings widget
        if elem.out == elem.OUT_POLY_AMOR:
            self.rbnPolyAmor.setChecked(True)
            for chk in self.ChecksPolyAmor:
                chk.setEnabled(True)
            for rbn in self.RbnsPolyAmor:
                rbn.setEnabled(True)
            for spins in self.SpinsSingle:
                spins.setEnabled(False)
        else:
            self.rbnSingleCryst.setChecked(True)
            for chk in self.ChecksPolyAmor:
                chk.setEnabled(False)
            for rbn in self.RbnsPolyAmor:
                rbn.setEnabled(False)
            for spins in self.SpinsSingle:
                spins.setEnabled(True)

        if elem.outAxisQ:
            self.chkAxQ.setChecked(True)
        if elem.outAxisD:
            self.chkAxD.setChecked(True)
        if elem.outAxis2Theta:
            self.chkAx2Theta.setChecked(True)

        if elem.separation == elem.SEP_XYZ:
            self.rbnXYZ.setChecked(True)
        elif elem.separation == elem.SEP_COH:
            self.rbnCoherent.setChecked(True)
        else:
            self.rbnNo.setChecked(True)

        self.omegaOffset.setValue(elem.omegaOffset)
        self.latticeA.setValue(elem.latticeA)
        self.latticeB.setValue(elem.latticeB)
        self.latticeC.setValue(elem.latticeC)
        self.latticeAlpha.setValue(elem.latticeAlpha)
        self.latticeBeta.setValue(elem.latticeBeta)
        self.latticeGamma.setValue(elem.latticeGamma)
        self.scatterU1.setValue(elem.scatterU1)
        self.scatterU2.setValue(elem.scatterU2)
        self.scatterU3.setValue(elem.scatterU3)
        self.scatterV1.setValue(elem.scatterV1)
        self.scatterV2.setValue(elem.scatterV2)
        self.scatterV3.setValue(elem.scatterV3)
