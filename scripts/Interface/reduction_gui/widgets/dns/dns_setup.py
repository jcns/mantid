from PyQt4.QtGui import QLineEdit, QPushButton, QTableView, QHeaderView, QCheckBox, QDoubleSpinBox, QRadioButton, \
    QLayout, QWidget, QSpacerItem, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGroupBox, QGridLayout, QButtonGroup, \
    QSizePolicy, QMessageBox
from PyQt4.QtCore import QAbstractTableModel, pyqtSignal, QModelIndex, Qt

from reduction_gui.widgets.base_widget import BaseWidget
from reduction_gui.reduction.dns.dns_reduction import DNSScriptElement


class DNSSetupWidget(BaseWidget):

    name = 'DNS Reduction'

    class DataTable(QAbstractTableModel):

        def __init__(self, parent):
            QAbstractTableModel.__init__(self, parent)
            self.tableData = []

        def _numRows(self):
            return len(self.tableData)

        def _getRow(self, row):
            return self.tableData[row] if row < self._numRows() else ('', '', '')

        def _isRowEmpty(self, row):
            (runs, outWs, comment) = self._getRow(row)
            return not str(runs).strip() and not str(outWs).strip() and not str(comment).strip()

        def _removeTrailingEmptyRows(self):
            for row in reversed(range(self._numRows())):
                if self._isRowEmpty(row):
                    del self.tableData[row]
                else:
                    break

        def _removeEmptyRows(self):
            for row in reversed(range(self._numRows())):
                if self._isRowEmpty(row):
                    del self.tableData[row]

        def _ensureHasRows(self, numRows):
            while self._numRows() < numRows:
                self.tableData.append(('', '', ''))

        def _setCellText(self, row, col, text):
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
            return str(self._getRow(row)[col]).strip()

        headers = ('Run numbers', 'Output Workspace', 'Comment')
        selectCell = pyqtSignal(int, int)

        def emptyCells(self, indexes):

            for index in indexes:
                row = index.row()
                col = index.column()

                self._setCellText(row, col, '')

            self._removeEmptyRows()
            self.reset()

            self.selectCell.emit(0, 0)

        def rowCount(self, _=QModelIndex()):
            return self._numRows() + 1

        def columnCount(self, _=QModelIndex()):
            return 3

        def headerData(self, selction, orientation, role):
            if Qt.Horizontal == orientation and Qt.DisplayRole == role:
                return self.headers[selction]

            return None

        def data(self, index, role):
            if Qt.DisplayRole == role or Qt.EditRole == role:
                return self._getCellText(index.row(), index.column())

            return None

        def setData(self, index, text, _):
            row = index.row()
            col = index.column()

            self._setCellText(row, col, text)
            self._removeTrailingEmptyRows()

            self.reset()

            col = col + 1

            if col >= 3:
                row = row + 1
                col = 0

            row = min(row, self.rowCount() - 1)
            self.selectCell.emit(row, col)

            return True

        def flags(self, _):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    class MaskDetTable(QAbstractTableModel):

        def __init__(self, parent):
            QAbstractTableModel.__init__(self, parent)
            self.tableData = []

        def _numRows(self):
            return len(self.tableData)

        def _getRow(self, row):
            return self.tableData[row] if row < self._numRows() else ('', '')

        def _isRowEmpty(self, row):
            (minAngle, maxAngle) = self._getRow(row)
            return not str(minAngle).strip() and not str(maxAngle).strip()

        def _removeTrailingEmptyRows(self):
            for row in reversed(range(self._numRows())):
                if self._isRowEmpty(row):
                    del self.tableData[row]
                else:
                    break

        def _removeEmptyRows(self):
            for row in reversed(range(self._numRows())):
                if self._isRowEmpty(row):
                    del self.tableData[row]

        def _ensureHasRows(self, numRows):
            while self._numRows() < numRows:
                self.tableData.append(('', ''))

        def _noMinAngle(self, row):
            if not self._isRowEmpty(row):
                (minAngle, maxAngle) = self.tableData[row]
                return not minAngle

        def _noMaxAngle(self, row):
            if not self._isRowEmpty(row):
                (minAngle, maxAngle) = self.tableData[row]
                return not maxAngle

        def _setCellText(self, row, col, text):

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

        headers = ('Min Angle[\305]', 'Max Angle[\305]')
        selectCell = pyqtSignal(int, int)

        def emptyCells(self, indexes):

            for index in indexes:
                row = index.row()
                col = index.column()

                self._setCellText(row, col, '')

            self._removeEmptyRows()
            self.reset()

            self.selectCell.emit(0, 0)

        def rowNoMinAngle(self):
            for i in range(len(self.tableData)):
                if self._noMinAngle(i):
                    return i
            return None

        def rowNoMaxAngle(self):
            for i in range(len(self.tableData)):
                if self._noMaxAngle(i):
                    return i
            return None

        def rowCount(self, _=QModelIndex()):
            return self._numRows() + 1

        def columnCount(self, _=QModelIndex()):
            return 2

        def headerData(self, selction, orientation, role):
            if Qt.Horizontal == orientation and Qt.DisplayRole == role:
                return self.headers[selction]

            return None

        def data(self, index, role):
            if Qt.DisplayRole == role or Qt.EditRole == role:
                return self._getCellText(index.row(), index.column())

            return None

        def setData(self, index, text, _):
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
            self.selectCell.emit(row, col)

            return True

        def flags(self, _):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    class TableViews(QTableView):

        def keyPressEvent(self, QKeyEvent):
            if QKeyEvent.key() == Qt.Key_Delete or QKeyEvent.key() == Qt.Key_Backspace:
                self.model().emptyCells(self.selectedIndexes())
            else:
                QTableView.keyPressEvent(self, QKeyEvent)


    TIP_sampleDataPath = ''
    TIP_btnSampleDataPath = ''
    TIP_sampleFilePre = ''
    TIP_sampleFileSuff = ''

    TIP_runsView = ''

    TIP_maskAngle = ''

    TIP_chkSaveToFile = ''
    TIP_outDir = ''
    TIP_btnOutDir = ''
    TIP_outFile = ''

    TIP_standardDataPath = ''
    TIP_btnStandardDataPath = ''

    TIP_chkDetEffi = ''
    TIP_chkSumVan = ''
    TIP_chkSubInst = ''
    TIP_subFac = ''
    TIP_chkFlippRatio = ''
    TIP_flippFac = ''
    TIP_multiSF = ''
    TIP_rbnNormaliseTime = ''
    TIP_rbnNormaliseMonitor = ''
    TIP_neutronWaveLen = ''

    TIP_rbnPolyAmor = ''
    TIP_rbnSingleCryst = ''
    TIP_chkAxQ = ''
    TIP_chkAxD = ''
    TIP_chkAx2Theta = ''
    TIP_rbnXYZ = ''
    TIP_rbnCoherent = ''
    TIP_rbnNo = ''
    TIP_omegaOffset = ''
    TIP_latticeA = ''
    TIP_latticeB = ''
    TIP_latticeC = ''
    TIP_latticeAlpha = ''
    TIP_latticeBeta = ''
    TIP_latticeGamma = ''
    TIP_scatterU1 = ''
    TIP_scatterU2 = ''
    TIP_scatterU3 = ''
    TIP_scatterV1 = ''
    TIP_scatterV2 = ''
    TIP_scatterV3 = ''

    def __init__(self, settings):

        BaseWidget.__init__(self, settings=settings)
        inf = float('inf')

        def tip(widget, text):
            if text:
                widget.setToolTip(text)
            return widget

        def set_spin(spin, minVal=-inf, maxVal=+inf):
            spin.setRange(minVal, maxVal)
            spin.setDecimals(2)
            spin.setSingleStep(0.01)

        def set_spin_lattice(spin, minVal=-inf, maxVal=+inf):
            spin.setRange(minVal, maxVal)
            spin.setDecimals(4)
            spin.setSingleStep(0.01)

        self.sampleDataPath = tip(QLineEdit(), self.TIP_sampleDataPath)
        self.btnSampleDataPath = tip(QPushButton('Browse'), self.TIP_btnSampleDataPath)
        self.sampleFilePre = tip(QLineEdit(), self.TIP_sampleFilePre)
        self.sampleFileSuff = tip(QLineEdit(), self.TIP_sampleFileSuff)

        self.runsView = tip(self.TableViews(self), self.TIP_runsView)
        self.runsView.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.runsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.runNumbersModel = DNSSetupWidget.DataTable(self)
        self.runsView.setModel(self.runNumbersModel)

        self.maskAngleView = tip(self.TableViews(self), self.TIP_maskAngle)
        self.maskAngleView.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.maskAngleView.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.maskAngleModel = DNSSetupWidget.MaskDetTable(self)
        self.maskAngleView.setModel(self.maskAngleModel)

        self.chkSaveToFile = tip(QCheckBox('Save to file'), self.TIP_chkSaveToFile)
        self.outDir = tip(QLineEdit(), self.TIP_outDir)
        self.btnOutDir = tip(QPushButton('Browse'), self.TIP_btnOutDir)
        self.outFile = tip(QLineEdit(), self.TIP_outFile)

        self.standardDataPath = tip(QLineEdit(), self.TIP_standardDataPath)
        self.btnStandardDataPath = tip(QPushButton('Browse'), self.TIP_btnStandardDataPath)

        self.chkdetEffi = tip(QCheckBox('Detector efficiency correction'), self.TIP_chkDetEffi)
        self.chksumVan = tip(QCheckBox('Sum Vanadium over detector position'), self.TIP_chkSumVan)
        self.chksubInst = tip(QCheckBox('Subtract instrument background for sample'), self.TIP_chkSubInst)
        self.subFac = tip(QDoubleSpinBox(), self.TIP_subFac)
        self.chkFlippRatio = tip(QCheckBox('Flipping ratio correction'), self.TIP_chkFlippRatio)
        self.flippFac = tip(QDoubleSpinBox(), self.TIP_flippFac)
        self.multiSF = tip(QDoubleSpinBox(), self.TIP_multiSF)
        self.rbnNormaliseTime = tip(QRadioButton('time'), self.TIP_rbnNormaliseTime)
        self.rbnNormaliseMonitor = tip(QRadioButton('monitor'), self.TIP_rbnNormaliseMonitor)
        self.neutronWaveLength = tip(QDoubleSpinBox(),  self.TIP_neutronWaveLen)
        set_spin(self.subFac, 0.0)
        set_spin(self.flippFac, 0.0)
        set_spin(self.multiSF, 0.0, 1.0)
        set_spin(self.neutronWaveLength, 0.0)

        self.rbnPolyAmor = tip(QRadioButton('Polycrystal/Amorphous'), self.TIP_rbnPolyAmor)
        self.chkAxQ = tip(QCheckBox('q'), self.TIP_chkAxQ)
        self.chkAxD = tip(QCheckBox('d'), self.TIP_chkAxD)
        self.chkAx2Theta = tip(QCheckBox(u'2\u0398'), self.TIP_chkAx2Theta)
        self.rbnXYZ = tip(QRadioButton('XYZ'), self.TIP_rbnXYZ)
        self.rbnCoherent = tip(QRadioButton('Coherent/Incoherent'), self.TIP_rbnCoherent)
        self.rbnNo = tip(QRadioButton('No'), self.TIP_rbnNo)

        self.rbnSingleCryst = tip(QRadioButton('Single Crystal'), self.TIP_rbnSingleCryst)
        self.omegaOffset = tip(QDoubleSpinBox(), self.TIP_omegaOffset)
        self.latticeA = tip(QDoubleSpinBox(), self.TIP_latticeA)
        self.latticeB = tip(QDoubleSpinBox(), self.TIP_latticeB)
        self.latticeC = tip(QDoubleSpinBox(), self.TIP_latticeC)
        self.latticeAlpha = tip(QDoubleSpinBox(), self.TIP_latticeAlpha)
        self.latticeAlpha.setMinimumWidth(75)
        self.latticeBeta = tip(QDoubleSpinBox(), self.TIP_latticeBeta)
        self.latticeBeta.setMinimumWidth(75)
        self.latticeGamma = tip(QDoubleSpinBox(), self.TIP_latticeGamma)
        self.latticeGamma.setMinimumWidth(75)
        self.scatterU1 = tip(QDoubleSpinBox(), self.TIP_scatterU1)
        self.scatterU2 = tip(QDoubleSpinBox(), self.TIP_scatterU2)
        self.scatterU3 = tip(QDoubleSpinBox(), self.TIP_scatterU3)
        self.scatterV1 = tip(QDoubleSpinBox(), self.TIP_scatterV1)
        self.scatterV2 = tip(QDoubleSpinBox(), self.TIP_scatterV2)
        self.scatterV3 = tip(QDoubleSpinBox(), self.TIP_scatterV3)
        set_spin(self.omegaOffset)
        set_spin_lattice(self.latticeA, 0)
        set_spin_lattice(self.latticeB, 0)
        set_spin_lattice(self.latticeC, 0)
        set_spin(self.latticeAlpha, 0)
        set_spin(self.latticeBeta, 0)
        set_spin(self.latticeGamma, 0)
        set_spin(self.scatterU1)
        set_spin(self.scatterU2)
        set_spin(self.scatterU3)
        set_spin(self.scatterV1)
        set_spin(self.scatterV2)
        set_spin(self.scatterV3)

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

        def _frame_box(frame, box) :
            frame.setFrameShape(QFrame.Box)
            frame.setLayout(box)

        gbSampleData = QGroupBox('Sample data')
        gbMaskDet = QGroupBox('Mask Detectors')
        gbOut = QGroupBox()
        gbStdData = QGroupBox('Standard data')
        gbDataRed = QGroupBox('Data reduction settings')
        gbOutput = QGroupBox()

        box = QHBoxLayout()
        self._layout.addLayout(box)

        sampleBox = vbox((gbSampleData, self.runsView))
        frameSampleBox = QFrame()
        _frame_box(frameSampleBox, sampleBox)

        maskDetectorBox = vbox((gbMaskDet,))
        frameMaskDetectorBox = QFrame()
        _frame_box(frameMaskDetectorBox, maskDetectorBox)

        outBox = vbox((self.chkSaveToFile, gbOut))
        frameOutBox = QFrame()
        _frame_box(frameOutBox, outBox)

        stdBox = vbox((gbStdData,))
        frameStdData = QFrame()
        _frame_box(frameStdData, stdBox)

        dataRedBox = vbox((gbDataRed,))
        frameDataRedBox = QFrame()
        _frame_box(frameDataRedBox, dataRedBox)

        OutputBox = vbox((gbOutput,))
        frameOutputBox = QFrame()
        _frame_box(frameOutputBox, OutputBox)

        box.addLayout(vbox((frameSampleBox, frameMaskDetectorBox, frameOutBox)))
        box.addLayout(vbox((frameStdData, frameDataRedBox, frameOutputBox)))

        grid = QGridLayout()
        hboxSampleData = hbox((QLabel('Data path'), self.sampleDataPath, self.btnSampleDataPath))
        grid.addLayout(hboxSampleData,         0, 0, 1, 4)
        grid.addWidget(QLabel('File prefix'),  1, 0)
        grid.addWidget(self.sampleFilePre,     1, 1)
        grid.addWidget(QLabel('suffix'),       1, 2)
        grid.addWidget(self.sampleFileSuff,    1, 3)
        gbSampleData.setLayout(grid)

        grid = QGridLayout()
        grid.addWidget(self.maskAngleView, 0, 0)
        gbMaskDet.setLayout(grid)

        self.SaveLines = []
        self.SaveLines.append(self.outDir)
        self.SaveLines.append(self.outFile)

        grid = QGridLayout()
        grid.addWidget(QLabel("       Output directory"),   1, 0)
        grid.addWidget(self.outDir,                         1, 1)
        grid.addWidget(self.btnOutDir,                      1, 2)
        grid.addWidget(QLabel('       Output file prefix'), 2, 0)
        grid.addWidget(self.outFile,                        2, 1)
        gbOut.setLayout(grid)
        gbOut.setContentsMargins(0, 0, 0, 0)

        grid = QGridLayout()
        grid.addWidget(QLabel('Path'),              1, 1)
        grid.addWidget(self.standardDataPath,       1, 2)
        grid.addWidget(self.btnStandardDataPath,    1, 3)
        gbStdData.setLayout(grid)

        bntGroup = QButtonGroup(self)
        bntGroup.addButton(self.rbnNormaliseMonitor)
        bntGroup.addButton(self.rbnNormaliseTime)

        spacerFac1 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        spacerFac2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)

        hboxSumVan = hbox((QLabel('      '), self.chksumVan,
                           QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hboxSubInst = hbox((QLabel('      '), QLabel('Factor'), self.subFac,
                            QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hboxFlipp = hbox((QLabel('      '), QLabel('Factor'), self.flippFac,
                          QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hboxMultiSP = hbox((QLabel('Multiple SF scattering probability'), self.multiSF,
                            QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hboxNormalise = hbox((QLabel('Normalization'), self.rbnNormaliseTime, self.rbnNormaliseMonitor,
                              QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hboxWaveLength = hbox((QLabel('Neutron wavelength (\305)'), self.neutronWaveLength,
                               QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        grid = QGridLayout()
        grid.addWidget(self.chkdetEffi,    0, 0, 1, 2)
        grid.addLayout(hboxSumVan,         1, 0, 1, 3)
        grid.addWidget(self.chksubInst,    2, 0, 1, 3)
        grid.addLayout(hboxSubInst,        3, 0, 1, 4)
        grid.addItem(spacerFac1,           4, 0)
        grid.addWidget(self.chkFlippRatio, 5, 0, 1, 2)
        grid.addLayout(hboxFlipp,          6, 0, 1, 4)
        grid.addItem(spacerFac2,           7, 0)
        grid.addLayout(hboxMultiSP,        8, 0, 1, 3)
        grid.addLayout(hboxNormalise,      9, 0, 1, 4)
        grid.addLayout(hboxWaveLength,    10, 0, 1, 3)
        gbDataRed.setLayout(grid)

        bntGroup = QButtonGroup(self)
        bntGroup.addButton(self.rbnPolyAmor)
        bntGroup.addButton(self.rbnSingleCryst)

        bntGroup = QButtonGroup(self)
        bntGroup.addButton(self.rbnXYZ)
        bntGroup.addButton(self.rbnCoherent)
        bntGroup.addButton(self.rbnNo)

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

        grid = QGridLayout()

        spacerRbn = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Minimum)

        hboxAx = hbox((self.chkAxQ, self.chkAxD, self.chkAx2Theta))
        hboxNormalise = hbox((self.rbnXYZ, self.rbnCoherent, self.rbnNo))
        hboxWaveLength = hbox((QLabel('Omega offset'), self.omegaOffset,
                               QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        hboxLatticeA = hbox((QLabel('a[\305]'), self.latticeA,
                             QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hboxLatticeB = hbox((QLabel('b[\305]'), self.latticeB,
                             QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))
        hboxLatticeC = hbox((QLabel('c[\305]'), self.latticeC,
                             QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        hboxLatticeAlpha = hbox((QLabel(u'\u03B1[\u00B0]'), self.latticeAlpha,
                                 QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        hboxLatticeBeta = hbox((QLabel(u'\u03B2[\u00B0]'),self.latticeBeta,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        hboxLatticeGamma = hbox((QLabel(u'\u03B3[\u00B0]'), self.latticeGamma,
                                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)))

        gridLattice = QGridLayout()
        gridLattice.addLayout(hboxLatticeA,     0, 0)
        gridLattice.addLayout(hboxLatticeB,     0, 1)
        gridLattice.addLayout(hboxLatticeC,     0, 2)
        gridLattice.addLayout(hboxLatticeAlpha, 1, 0)
        gridLattice.addLayout(hboxLatticeBeta,  1, 1)
        gridLattice.addLayout(hboxLatticeGamma, 1, 2)

        hboxScatterV = hbox((QLabel('v'), self.scatterV1, self.scatterV2, self.scatterV3))
        hboxScatterU = hbox((QLabel('u'), self.scatterU1, self.scatterU2, self.scatterU3, hboxScatterV))

        grid.addWidget(self.rbnPolyAmor,             0, 0, 1, 2)
        grid.addWidget(QLabel('Abscissa'),           1, 1)
        grid.addLayout(hboxAx,                       2, 1, 1, 3)
        grid.addWidget(QLabel('Separation'),         3, 1)
        grid.addLayout(hboxNormalise,                4, 1)
        grid.addItem(spacerRbn,                      5, 0)
        grid.addWidget(self.rbnSingleCryst,          6, 0, 1, 2)
        grid.addLayout(hboxWaveLength,               7, 1, 1, 2)
        grid.addWidget(QLabel("Lattice parameters"), 8, 1)
        grid.addLayout(gridLattice,                  9, 1)
        grid.addWidget(QLabel('Scattering Plane'),  11, 1)
        grid.addLayout(hboxScatterU,                12, 1, 1, 4)

        gbOutput.setLayout(grid)
        gbOutput.setContentsMargins(0, 0, 0, 0)

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

        dirname = self.dir_browse_dialog()
        if dirname:
            self.sampleDataPath.setText(dirname)

    def _onSelectedCell(self, row, column):
        index = self.runNumbersModel.index(row, column)
        self.runsView.setCurrentIndex(index)
        self.runsView.setFocus()

    def _onSelectedCellMask(self, row, column):
        index = self.maskAngleModel.index(row, column)
        self.maskAngleView.setCurrentIndex(index)
        self.maskAngleView.setFocus()

    def _saveFileChanged(self):
        if self.chkSaveToFile.isChecked():
            self._SaveFileChecked()
        else:
            self._SaveFileNotChecked()

    def _outputDir(self):

        dirname = self.dir_browse_dialog()
        if dirname:
            self.outDir.setText(dirname)

    def _stdDataDir(self):

        dirname = self.dir_browse_dialog()

        if dirname:
            self.standardDataPath.setText(dirname)

    def _detEffiChanged(self):
        # Disable sum vanadium over detector position
        self.chksumVan.setEnabled(False)
        #if self.chkdetEffi.isChecked():
        #    self.chksumVan.setEnabled(True)
        #else:
        #    self.chksumVan.setEnabled(False)

    def _subInstChanged(self):
        if self.chksubInst.isChecked():
            self.subFac.setEnabled(True)
        else:
            self.subFac.setEnabled(False)

    def _flippRatioChanged(self):
        if self.chkFlippRatio.isChecked():
            self.flippFac.setEnabled(True)
        else:
            self.flippFac.setEnabled(False)

    def _rbnOutChanged(self):
        if self.rbnSingleCryst.isChecked():
            self._SingleChecked()
            self._PolyAmorNotChecked()
        elif self.rbnPolyAmor.isChecked():
            self._SingleNotChecked()
            self._PolyAmorChecked()

    def _SaveFileChecked(self):

        for line in self.SaveLines:
            line.setDisabled(False)

        self.btnOutDir.setEnabled(True)

    def _SaveFileNotChecked(self):

        for line in self.SaveLines:
            line.setDisabled(True)

        self.btnOutDir.setEnabled(False)

    def _SingleChecked(self):

        for spin in self.SpinsSingle:
            spin.setEnabled(True)

    def _PolyAmorChecked(self):

        for chkButton in self.ChecksPolyAmor:
            chkButton.setEnabled(True)

        for rbn in self.RbnsPolyAmor:
            rbn.setEnabled(True)

    def _SingleNotChecked(self):

        for spin in self.SpinsSingle:
            spin.setEnabled(False)

    def _PolyAmorNotChecked(self):

        for chkButton in self.ChecksPolyAmor:
            chkButton.setEnabled(False)

        for rbn in self.RbnsPolyAmor:
            rbn.setEnabled(False)

    def get_state(self):

        elem = DNSScriptElement()

        def line_text(lineEdit):
            return lineEdit.text().strip()

        elem.facility_name = self._settings.facility_name
        elem.instrument_name = self._settings.instrument_name

        elem.sampleDataPath = line_text(self.sampleDataPath)
        elem.filePrefix = line_text(self.sampleFilePre)
        elem.fileSuffix = line_text(self.sampleFileSuff)

        elem.dataRuns = self.runNumbersModel.tableData

        elem.maskAngles = self.maskAngleModel.tableData

        elem.saveToFile = self.chkSaveToFile.isChecked()
        elem.outDir = line_text(self.outDir)
        elem.outPrefix = line_text(self.outFile)

        elem.standardDataPath = line_text(self.standardDataPath)

        elem.detEffi = self.chkdetEffi.isChecked()
        elem.sumVan = self.chksumVan.isChecked()
        elem.subInst = self.chksubInst.isChecked()
        elem.subFac = self.subFac.value()
        elem.flippRatio = self.chkFlippRatio.isChecked()
        elem.flippFac = self.flippFac.value()
        elem.multiSF = self.multiSF.value()
        elem.normalise = elem.NORM_TIME if self.rbnNormaliseTime.isChecked() else \
            elem.NORM_MONITOR
        elem.neutronWaveLen = self.neutronWaveLength.value()

        elem.out = elem.OUT_POLY_AMOR if self.rbnPolyAmor.isChecked() else \
            elem.OUT_SINGLE_CRYST

        elem.outAxisQ = self.chkAxQ.isChecked()
        elem.outAxisD = self.chkAxD.isChecked()
        elem.outAxis2Theta = self.chkAx2Theta.isChecked()
        elem.separation = elem.SEP_XYZ if self.rbnXYZ.isChecked() else \
            elem.SEP_COH if self.rbnCoherent.isChecked() else elem.SEP_NO

        elem.omegaOffset = self.omegaOffset.value()
        elem.latticeA = self.latticeA.value()
        elem.latticeB = self.latticeB.value()
        elem.latticeC = self.latticeC.value()
        elem.latticeAlpha = self.latticeAlpha.value()
        elem.latticeBeta = self.latticeBeta.value()
        elem.latticeGamma = self.latticeGamma.value()
        elem.scatterU1 = self.scatterU1.value()
        elem.scatterU2 = self.scatterU2.value()
        elem.scatterU3 = self.scatterU3.value()
        elem.scatterV1 = self.scatterV1.value()
        elem.scatterV2 = self.scatterV2.value()
        elem.scatterV3 = self.scatterV3.value()

        return elem

    def set_state(self, dnsScriptElement):

        elem = dnsScriptElement

        if self.maskAngleModel.rowNoMinAngle():
            message = "No min Angle in row: " + str(self.maskAngleModel.rowNoMinAngle())
            message += " , using default: 0.0"
            QMessageBox.warning(self, "Warning", message)

        if self.maskAngleModel.rowNoMaxAngle():
            message = "No max Angle in row: " + str(self.maskAngleModel.rowNoMaxAngle())
            message += " , using default: 180.0"
            QMessageBox.warning(self, "Warining", message)

        self.sampleDataPath.setText(elem.sampleDataPath)
        self.sampleFilePre.setText(elem.filePrefix)
        self.sampleFileSuff.setText(elem.fileSuffix)

        self.runNumbersModel.tableData = elem.dataRuns
        self.runNumbersModel.reset()

        self.maskAngleModel.tableData = elem.maskAngles
        self.maskAngleModel.reset()

        self.chkSaveToFile.setChecked(elem.saveToFile)

        self.outDir.setText(elem.outDir)
        self.outFile.setText(elem.outPrefix)

        if self.chkSaveToFile.isChecked():
            for line in self.SaveLines:
                line.setDisabled(False)
        else:
            for line in self.SaveLines:
                line.setDisabled(True)

        self.standardDataPath.setText(elem.standardDataPath)

        self.chkdetEffi.setChecked(elem.detEffi)
        self.chksumVan.setChecked(elem.sumVan)
        # Deaktivate Sum Vanadium Option
        self.chksumVan.setEnabled(False)
        #if self.chkdetEffi.isChecked():
        #    self.chksumVan.setEnabled(True)
        #else:
        #    self.chksumVan.setEnabled(False)
        self.chksubInst.setChecked(elem.subInst)
        self.subFac.setValue(elem.subFac)
        if self.chksubInst.isChecked():
            self.subFac.setEnabled(True)
        else:
            self.subFac.setEnabled(False)
        self.chkFlippRatio.setChecked(elem.flippRatio)
        self.flippFac.setValue(elem.flippFac)
        if self.chkFlippRatio.isChecked():
            self.flippFac.setEnabled(True)
        else:
            self.flippFac.setEnabled(False)
        self.multiSF.setValue(elem.multiSF)
        self.multiSF.setEnabled(False)
        if elem.normalise == elem.NORM_TIME:
            self.rbnNormaliseTime.setChecked(True)
        elif elem.normalise == elem.NORM_MONITOR:
            self.rbnNormaliseMonitor.setChecked(True)
        self.neutronWaveLength.setValue(elem.neutronWaveLen)

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
