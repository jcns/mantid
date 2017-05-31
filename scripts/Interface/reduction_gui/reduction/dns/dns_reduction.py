import xml.dom.minidom

from collections import OrderedDict
import os
import re
import numpy as np

from mantid.kernel import *
from mantid.api import *

from reduction_gui.reduction.scripter import BaseScriptElement, BaseReductionScripter
import mantid.simpleapi as api


class DNSScriptElement(BaseScriptElement):

    # normalization
    NORM_TIME = 0
    NORM_MONITOR = 1

    OUT_POLY_AMOR = 0
    OUT_SINGLE_CRYST = 1

    # separation
    SEP_XYZ = 0
    SEP_COH = 1
    SEP_NO = 2

    DEF_SaveToFile = False

    DEF_DetEffi = True
    DEF_SumVan = False
    DEF_SubInst = True
    DEF_SubFac = 1.0
    DEF_FlippRatio = True
    DEF_FlippFac = 1.0
    DEF_MultiSF = 0.0
    DEF_Normalise = NORM_TIME
    DEF_NeutWaveLen = 0.0
    #DEF_Intermediate = False

    DEF_Output = OUT_POLY_AMOR

    DEF_OutAxisQ = True
    DEF_OutAxisD = True
    DEF_OutAxis2Theta = True
    DEF_Separation = SEP_XYZ

    DEF_OmegaOffset = 0.0
    DEF_LatticeA = 0.0
    DEF_LatticeB = 0.0
    DEF_LatticeC = 0.0
    DEF_LatticeAlpha = 0.0
    DEF_LatticeBeta = 0.0
    DEF_LatticeGamma = 0.0
    DEF_ScatterU1 = 0.0
    DEF_ScatterU2 = 0.0
    DEF_ScatterU3 = 0.0
    DEF_ScatterV1 = 0.0
    DEF_ScatterV2 = 0.0
    DEF_ScatterV3 = 0.0

    XML_TAG = 'DNSReduction'

    def reset(self):

        self.facility_name = ''
        self.instrument_name = ''

        self.sampleDataPath = ''
        self.filePrefix = ''
        self.fileSuffix = ''

        self.dataRuns = []

        self.maskAngles = []

        self.saveToFile = self.DEF_SaveToFile
        self.outDir = ''
        self.outPrefix = ''

        self.standardDataPath = ''

        self.detEffi = self.DEF_DetEffi
        self.sumVan = self.DEF_SumVan
        self.subInst = self.DEF_SubInst
        self.subFac = self.DEF_SubFac
        self.flippRatio = self.DEF_FlippRatio
        self.flippFac = self.DEF_FlippFac
        self.multiSF = self.DEF_MultiSF
        self.normalise = self.DEF_Normalise
        self.neutronWaveLen = self.DEF_NeutWaveLen

        self.out = self.DEF_Output

        self.outAxisQ = self.DEF_OutAxisQ
        self.outAxisD = self.DEF_OutAxisD
        self.outAxis2Theta = self.DEF_OutAxis2Theta
        self.separation = self.DEF_Separation

        self.omegaOffset = self.DEF_OmegaOffset
        self.latticeA = self.DEF_LatticeA
        self.latticeB = self.DEF_LatticeB
        self.latticeC = self.DEF_LatticeC
        self.latticeAlpha = self.DEF_LatticeAlpha
        self.latticeBeta = self.DEF_LatticeBeta
        self.latticeGamma = self.DEF_LatticeGamma
        self.scatterU1 = self.DEF_ScatterU1
        self.scatterU2 = self.DEF_ScatterU2
        self.scatterU3 = self.DEF_ScatterU3
        self.scatterV1 = self.DEF_ScatterV1
        self.scatterV2 = self.DEF_ScatterV2
        self.scatterV3 = self.DEF_ScatterV3

    def to_xml(self):

        res =['']

        def put(tag, val):
            res[0] += ' <{0}>{1}</{0}>\n'.format(tag, str(val))

        put('sample_data_path', self.sampleDataPath)
        put('file_prefix',      self.filePrefix)
        put('file_suffix',      self.fileSuffix)

        for (runs, ws, cmnt) in self.dataRuns:
            put('data_runs',             runs)
            put('data_output_workspace', ws)
            put('data_comment',          cmnt)

        for (min, max) in self.maskAngles:
            put('mask_min_Angle', min)
            put('mask_max_Angle', max)

        put('save_to_file',       self.saveToFile)
        put('output_directory',   self.outDir)
        put('output_file_prefix', self.outPrefix)

        put('standard_data_path', self.standardDataPath)

        put('detector_efficiency',        self.detEffi)
        put('sum_Vanadium',               self.sumVan)
        put('subtract_instrument',        self.subInst)
        put('subtract_instrument_factor', self.subFac)
        put('flipping_ratio',             self.flippRatio)
        put('flipping_ratio_factor',      self.flippFac)
        put('multiple_SF_scattering',     self.multiSF)
        put('normalise',                  self.normalise)
        put('neutron_wave_length',        self.neutronWaveLen)

        put('output',             self.out)

        put('output_Axis_q',      self.outAxisQ)
        put('output_Axis_d',      self.outAxisD)
        put('output_Axis_2Theta', self.outAxis2Theta)
        put('separation',         self.separation)

        put('lattice_parameters_a',     self.latticeA)
        put('lattice_parameters_b',     self.latticeB)
        put('lattice_patameters_c',     self.latticeC)
        put('lattice_patameters_alpha', self.latticeAlpha)
        put('lattice_parameters_beta',  self.latticeBeta)
        put('lattice_parameters_gamma', self.latticeGamma)
        put('scattering_Plane_u_1',     self.scatterU1)
        put('scattering_Plane_u_2',     self.scatterU2)
        put('scattering_Plane_u_3',     self.scatterU3)
        put('scattering_Plane_v_1',     self.scatterV1)
        put('scattering_Plane_v_2',     self.scatterV2)
        put('scattering_Plane_v_3',     self.scatterV3)

        return '<{0}>\n{1}</{0}>\n'.format(self.XML_TAG, res[0])

    def from_xml(self, xmlStr):

        self.reset()

        dom = xml.dom.minidom.parseString(xmlStr)
        els = dom.getElementsByTagName(self.XML_TAG)

        if els:

            dom = els[0]

            def get_str(tag, default=''):
                return BaseScriptElement.getStringElement(dom, tag, default=default)

            def get_int(tag, default):
                return BaseScriptElement.getIntElement(dom, tag, default=default)

            def get_flt(tag, default):
                return BaseScriptElement.getFloatElement(dom, tag, default=default)

            def get_strlst(tag):
                return BaseScriptElement.getStringList(dom, tag)

            def get_bol(tag, default):
                return BaseScriptElement.getBoolElement(dom, tag, default=default)

            self.sampleDataPath = get_str('sample_data_path')
            self.filePrefix = get_str('file_prefix')
            self.fileSuffix = get_str('file_suffix')

            dataRuns = get_strlst('data_runs')
            dataOutWs = get_strlst('data_output_workspace')
            dataCmts = get_strlst('data_comment')

            for i in range(min(len(dataRuns), len(dataOutWs), len(dataCmts))):
                self.dataRuns.append((dataRuns[i], dataOutWs[i], dataCmts[i]))

            maskMin = get_strlst('mask_min_Angle')
            maskMax = get_strlst('mask_max_Angle')

            for i in range(min(len(maskMin), len(maskMax))):
                self.maskAngles.append((maskMin[i], maskMax[i]))

            self.saveToFile = get_bol('save_to_file', self.DEF_SaveToFile)
            self.outDir = get_str('output_directory')
            self.outPrefix = get_str('output_file_prefix')

            self.standardDataPath = get_str('standard_data_path')

            self.detEffi = get_bol('detector_efficiency', self.DEF_DetEffi)
            self.sumVan = get_bol('sum_Vanadium', self.DEF_SumVan)
            self.subInst = get_bol('subtract_instrument', self.DEF_SubInst)
            self.subFac = get_flt('subtract_instrument_factor', self.subFac)
            self.flippRatio = get_bol('flipping_ratio', self.DEF_FlippRatio)
            self.multiSF = get_flt('multiple_SF_scattering', self.DEF_MultiSF)
            self.normalise = get_int('normalise', self.DEF_Normalise)
            self.neutronWaveLen = get_flt('neutron_wave_length', self.DEF_NeutWaveLen)

            self.out = get_int('output', self.DEF_Output)

            self.outAxisQ = get_bol('output_Axis_q', self.DEF_OutAxisQ)
            self.outAxisD = get_bol('output_Axis_d', self.DEF_OutAxisD)
            self.outAxis2Theta = get_bol('output_Axis_2Theta', self.DEF_OutAxis2Theta)
            self.separation = get_int('separation', self.DEF_Separation)

            self.latticeA = get_flt('lattice_parameters_a', self.DEF_LatticeA)
            self.latticeB = get_flt('lattice_parameters_b', self.DEF_LatticeB)
            self.latticeC = get_flt('lattice_parameters_c', self.DEF_LatticeC)
            self.latticeAlpha = get_flt('lattice_parameters_alpha', self.DEF_LatticeAlpha)
            self.latticeBeta = get_flt('lattice_parameters_beta', self.DEF_LatticeBeta)
            self.latticeGamma = get_flt('lattice_parameters_gamma', self.DEF_LatticeGamma)
            self.scatterU1 = get_flt('scattering_Plane_u_1', self.DEF_ScatterU1)
            self.scatterU2 = get_flt('scattering_Plane_u_2', self.DEF_ScatterU2)
            self.scatterU3 = get_flt('scattering_Plane_u_3', self.DEF_ScatterU3)
            self.scatterV1 = get_flt('scattering_Plane_v_1', self.DEF_ScatterV1)
            self.scatterV2 = get_flt('scattering_Plane_v_2', self.DEF_ScatterV2)
            self.scatterV3 = get_flt('scattering_Plane_v_3', self.DEF_ScatterV3)


    def to_script(self):

        def error(message):
            raise RuntimeError('DNS reduction error: ' + message)

        def _search_file(path, name):
            files = os.listdir(path)
            for file in files:
                if file.__contains__(name):
                    return True
            return False

        def _search_fs(path, prefix, suffix, runnumbers):
            numbers = runnumbers.split(",")
            fs = []
            found = False
            for runnumber in numbers:
                if runnumber.__contains__(":"):
                    (start, stop) = runnumber.split(":")
                    start = int(start)
                    stop = int(stop)
                    for i in range(start, stop+1):
                        for f in os.listdir(path):
                            if re.match(r"{}0*{}{}.d_dat".format(prefix, int(i), suffix), f):
                                found = True
                                fs.append(str(f))
                        if not found:
                            error('file with prefix ' + prefix + ', run number '
                                  + str(i) + ' and suffix ' + suffix + ' not found')
                        found = False
                else:
                    for f in os.listdir(path):
                        if re.match(r"{}0*{}{}.d_dat".format(prefix, int(runnumber), suffix), f):
                            found = True
                            fs.append(str(f))
                    if not found:
                        error('file with prefix ' + prefix + ", run number "
                              + str(runnumber) + " and suffix " + suffix + " not found")
                    found = False

            return fs

        if not os.path.lexists(self.sampleDataPath):
            error('sample data path not found')

        if not self.filePrefix:
            error('missing sample data file prefix')

        if not self.fileSuffix:
            error('missing sample data file suffix')

        (first_runs, first_workspace, first_comment) = self.dataRuns[0]
        if not self.dataRuns:
            error('Missing sample data runs')
        elif not first_runs and not first_workspace and not first_comment:
            error("First line empty")

        for (runs, workspace, comment) in self.dataRuns:
            if not runs:
                error("All rows must contain run numbers")
            elif runs and not workspace:
                error("There must be a workspace to all run numbers")

        for i in range(len(self.maskAngles)):
            (minA, maxA) = self.maskAngles[i]
            if not maxA:
                maxA = 180
            elif not minA:
                minA = 0

            if float(minA) < 0.0 or float(minA) > 180.0:
                errormess = "Angle must be between 0.0 and 180.0 (error in row " + str(i+1) + ' min angle)'
                error(errormess)

            if float(maxA) < 0.0 or float(maxA) > 180.0:
                errormess = "Angle must be between 0.0 and 180.0 (error in row " + str(i+1) + ' max angle)'
                error(errormess)

            if not float(minA) < float(maxA):
                errormess = 'Min Angle must be smaller than max Angle (error in row ' + str(i+1) + ')'
                error(errormess)

        if self.saveToFile:
            if not os.path.lexists(self.outDir):
                error('output directory not found')
            elif not os.access(self.outDir, os.W_OK):
                error('cant write in directory ' + str(self.outDir))

            if not self.outPrefix:
                error('missing output file prefix')

        if not os.path.lexists(self.standardDataPath):
            error('standard data path not found')
        else:
            tmp = api.LoadEmptyInstrument(InstrumentName='DNS')
            instrument = tmp.getInstrument()
            api.DeleteWorkspace(tmp)
            if self.detEffi:
                detEffiFilename = instrument.getStringParameter("vana")[0]
                found = _search_file(self.standardDataPath, detEffiFilename)
                if not found:
                    error('no file for detector efficiency correction in '
                          + str(self.standardDataPath) + ' found')
            if self.subInst:
                subInstFilename = instrument.getStringParameter("bkg")[0]
                found = _search_file(self.standardDataPath, subInstFilename)
                if not found:
                    error('no file to substract of instrument background for sample in '
                          + str(self.standardDataPath) + ' found')
            if self.flippRatio:
                flippRatioFilename = instrument.getStringParameter("nicr")[0]
                found = _search_file(self.standardDataPath, flippRatioFilename)
                if not found:
                    error('no file for flipping ratio correction in '
                          + str(self.standardDataPath) + ' found')

        if self.out == self.OUT_POLY_AMOR and not self.outAxisQ and not self.outAxisD and not self.outAxis2Theta:
            error('no abscissa selected')

        parameters = OrderedDict()

        sampleData = OrderedDict()

        sampleData['Data path'] = self.sampleDataPath
        sampleData['File prefix'] = self.filePrefix
        sampleData['File suffix'] = self.fileSuffix
        runs = OrderedDict()
        workspaces = []
        _files = []
        comments = []
        for i in range(len(self.dataRuns)):
            run = OrderedDict()
            (runNumber, outWs, comment) = self.dataRuns[i]
            workspaces.append(str(outWs))
            _files.append(_search_fs(self.sampleDataPath, self.filePrefix, self.fileSuffix, runNumber))
            comments.append(str(comment))
            run["Run numbers"] = runNumber
            run["Output Workspace"] = outWs
            run["Comment"] = comment
            string = "Runs in row: " + str(i)
            runs[string] = run

        sampleData['Data Table'] = runs

        parameters['Sample Data'] = sampleData

        maskDet = OrderedDict()
        for i in range(len(self.maskAngles)):
            mask = OrderedDict()
            (minA, maxA) = self.maskAngles[i]
            mask['Min Angle'] = minA
            mask['Max Angle'] = maxA
            string = "Angles row: " + str(i)
            maskDet[string] = mask

        parameters['Mask Detectors'] = maskDet

        saveToFile = OrderedDict()

        saveToFile['Save to file?'] = str(self.saveToFile)
        if self.saveToFile:
            saveToFile['Output directory'] = self.outDir
            saveToFile['Output file prefix'] = self.outPrefix

        parameters['Save'] = saveToFile

        stdData = OrderedDict()

        stdData['Path'] = self.standardDataPath

        parameters['Standard Data'] = stdData

        datRedSettings = OrderedDict()

        datRedSettings['Detector efficiency correction'] = str(self.detEffi)
        datRedSettings['Sum Vandium over detector position'] = str(self.sumVan)
        datRedSettings['Substract instrument background for sample'] = str(self.subInst)
        if self.subInst:
            datRedSettings['Substract factor'] = self.subFac
        datRedSettings['Flipping ratio correction'] = str(self.flippRatio)
        if self.flippRatio:
            datRedSettings['Flipping ratio factor'] = self.flippFac
        datRedSettings['Multiple SF scattering probability'] = self.multiSF
        if self.normalise == self.NORM_MONITOR:
            norm = 'monitor'
        else:
            norm = 'time'
        datRedSettings['Normalization'] = norm
        datRedSettings['Neutron wavelength'] = self.neutronWaveLen

        parameters['Data reduction settings'] = datRedSettings

        type = OrderedDict()

        if self.out == self.OUT_POLY_AMOR:
            type['Type'] = 'Polycrystal/Amorphous'
            outAx = []
            if self.outAxisQ:
                outAx.append('|Q|')

            if self.outAxisD:
                outAx.append('d-Spacing')

            if self.outAxis2Theta:
                outAx.append('2theta')

            type['Abscissa'] = str(outAx)
            if self.separation == self.SEP_XYZ:
                type['Separation'] = 'XYZ'
            elif self.separation == self.SEP_COH:
                type['Separation'] = 'Coherent/Incoherent'
            else:
                type['Separation'] = 'No'

        if self.out == self.OUT_SINGLE_CRYST:
            type['Type'] = 'Single Crystal'

            type['Omega offset'] = self.omegaOffset

            lattice = {}
            lattice['a'] = self.latticeA
            lattice['b'] = self.latticeB
            lattice['c'] = self.latticeC
            lattice['alpha'] = self.latticeAlpha
            lattice['beta'] = self.latticeBeta
            lattice['gamma'] = self.latticeGamma

            type['Lattice parameters'] = lattice

            scatter = {}
            u = []
            u.append(self.scatterU1)
            u.append(self.scatterU2)
            u.append(self.scatterU3)
            v = []
            v.append(self.scatterV1)
            v.append(self.scatterV2)
            v.append(self.scatterV3)
            scatter['u'] = u
            scatter['v'] = v

            type['Scattering Plane'] = scatter

        parameters['Sample'] = type

        print(str(parameters))

        script = ['']

        def l(line=''):
            script[0] += line + '\n'

        l("import numpy as np")
        l("import os")
        l()
        l("def is_in_list(angle_list, angle, tolerance):")
        l("    for a in angle_list:")
        l("        if np.fabs(a - angle) < tolerance:")
        l("            return True")
        l("    return False")
        l()
        l("def extract_norm_workspace(wsgroup):")
        l("    norm_dict = {'time': 'duration', 'monitor': 'mon_sum'}")
        l("    normlist = []")
        l("    for i in range(wsgroup.getNumberOfEntries()):")
        l("        ws = wsgroup.getItem(i)")
        l("        normws = CloneWorkspace(ws, OutputWorkspace= ws.getName() + '_norm')")
        l("        val = ws.getRun().getProperty(norm_dict[norm]).value")
        l("        for i in range(len(normws.extractY())):")
        l("            normws.setY(i, np.array([val]))")
        l("            normws.setE(i, np.array([0.0]))")
        l("        normlist.append(normws.getName())")
        l("    print str(normlist)")
        l("    GroupWorkspaces(normlist, OutputWorkspace=wsgroup.getName() + '_norm')")
        l()
        l("def merge_and_normalize(wsgroup, namex = ''):")
        l("    for x in xax:")
        l("        print 'merge and normailze'")
        l("        data_merged = DNSMergeRuns(wsgroup + namex, x, OutputWorkspace=wsgroup + '_m0' + '_' + x)")
        l("        norm_merged = DNSMergeRuns(wsgroup + '_norm' + namex, x, OutputWorkspace=wsgroup + '_norm_m' + '_' + x)")
        l("        try:")
        l("            Divide(data_merged, norm_merged, OutputWorkspace=wsgroup + '_m' + '_' + x)")
        l("        except:")
        l("            dataX = data_merged.extractX()")
        l("            norm_merged.setX(0, dataX[0])")
        l("            Divide(data_merged, norm_merged, OutputWorkspace=wsgroup+'_m'+ '_' + x)")
        l()
        l("config['default.facility'] = '{}'".format(self.facility_name))
        l("config['default.instrument'] = '{}'".format(self.instrument_name))
        l()
        l("tol = 0.5")
        l()
        l("datapath = '{}'".format(parameters['Sample Data']['Data path']))
        l("prefix = '{}'".format(parameters['Sample Data']['File prefix']))
        l("suffix = '{}'".format(parameters['Sample Data']['File suffix']))
        l("files = {}".format(_files))
        l("workspaces = {}".format(workspaces))
        l("comments = {}".format(comments))
        l("xax = {}".format(parameters['Sample']['Abscissa']))
        l("flipper_bool = {}".format(parameters['Data reduction settings']['Flipping ratio correction']))
        l()
        l("norm = '{}'".format(parameters['Data reduction settings']['Normalization']))
        l("stdpath = '{}'".format(parameters['Standard Data']['Path']))
        l()
        l("logger.debug(str(files))")
        l("for files_run in range(len(files)):")
        l("    files_run_str = ', '.join(files[files_run])")
        l("    logger.debug(files_run_str)")
        l("    logger.debug(files_run_str)")
        l("    DNSLoadData(FilesList=files_run_str, DataPath=datapath, OutWorkspaceName=workspaces[files_run],"
          "                OutputTable='SampleDataTable')")
        l("    sample_table = mtd[workspaces[files_run]+'_SampleDataTable']")
        l("    DNSLoadData(StandardType='vana', RefWorkspaces=sample_table, DataPath=stdpath, "
          "                OutWorkspaceName=workspaces[files_run], OutputTable='VanaDataTable')")
        l("    DNSLoadData(StandardType='nicr', RefWorkspaces=sample_table, DataPath=stdpath, "
          "                OutWorkspaceName=workspaces[files_run], OutputTable='NicrDataTable')")
        l("    DNSLoadData(StandardType='leer', RefWorkspaces=sample_table, DataPath=stdpath,"
          "                OutWorkspaceName=workspaces[files_run], OutputTable='BackgroundDataTable')")
        l("    DNSProcessStandardData(SampleTable=workspaces[files_run]+'_SampleDataTable', "
          "                           VanaTable=workspaces[files_run]+'_VanaDataTable', "
          "                           NiCrTable=workspaces[files_run]+'_NicrDataTable', "
          "                           BackgroundTable=workspaces[files_run]+'_BackgroundDataTable', "
          "                           OutputTable='ProcessedDataTable', OutWorkspaceName=workspaces[files_run])")
        l("    DNSProcessVanadium(VanadiumTable=workspaces[files_run]+'_VanaDataTable',"
          "                       BackgroundTable=workspaces[files_run]+'_BackgroundDataTable',"
          "                       SampleTable=workspaces[files_run]+'_SampleDataTable', "
          "                       OutWorkspaceName = workspaces[files_run])")
        """l("for run_table in range(len(workspaces)):")
        l("    logger.debug(str(workspaces[run_table]))")
        l("    dataworkspaces = []")
        l("    out_ws = workspaces[run_table]")
        l("    print ('outws = ' + str(out_ws))")
        l("    files_run = files[run_table]")
        l("    print ('files = ' + str(files_run))")
        l("    comment = comments[run_table]")
        l("    print ('comment = ' + str(comment))")
        l()
        l("    # 1. Load Sample Data")
        l("    for f in files_run:")
        l("        wname = os.path.splitext(f)[0]")
        l("        print wname")
        l("        filepath = os.path.join(datapath, f)")
        l("        print filepath")
        l("        LoadDNSLegacy(Filename=filepath, OutputWorkspace=wname, Normalization ='no')")
        l("        dataworkspaces.append(wname)")
        l("    print(str(dataworkspaces))")
        l("    allcalibrationworkspaces = []")
        l("    for f in os.listdir(stdpath):")
        l("        fullfilename = os.path.join(stdpath, f)")
        l("        if os.path.isfile(fullfilename):")
        l("            wname = os.path.splitext(f)[0]")
        l("            print wname")
        l("            if not mtd.doesExist(wname):")
        l("                LoadDNSLegacy(Filename=fullfilename, OutputWorkspace=wname, Normalization='no')")
        l("                allcalibrationworkspaces.append(wname)")
        l("    refws = mtd[dataworkspaces[0]]")
        l("    print(refws)")
        l("    coil_currents = 'C_a,C_b,C_c,C_z'")
        l("    calibrationworkspaces = []")
        l("    for wsname in allcalibrationworkspaces:")
        l("        result = CompareSampleLogs([refws.getName(), wsname], coil_currents, 0.01)")
        l("        if result:")
        l("            DeleteWorkspace(wsname)")
        l("        else:")
        l("            calibrationworkspaces.append(wsname)")
        l("    print(str(refws))")
        l("    print allcalibrationworkspaces")
        l("    print (str(calibrationworkspaces))")
        l("    deterota = []")
        l("    for wsname in dataworkspaces:")
        l("        angle = mtd[wsname].getRun().getProperty('deterota').value")
        l("        if not is_in_list(deterota, angle, tol):")
        l("            deterota.append(angle)")
        l("    logger.information('Detector rotation angles: ' + str(deterota))")
        l("    rawdata_x_sf = dict.fromkeys(deterota)")
        l("    rawdata_y_sf = dict.fromkeys(deterota)")
        l("    rawdata_z_sf = dict.fromkeys(deterota)")
        l("    rawdata_x_nsf = dict.fromkeys(deterota)")
        l("    rawdata_y_nsf = dict.fromkeys(deterota)")
        l("    rawdata_z_nsf = dict.fromkeys(deterota)")
        l("    rawvana_x_sf = dict.fromkeys(deterota)")
        l("    rawvana_y_sf = dict.fromkeys(deterota)")
        l("    rawvana_z_sf = dict.fromkeys(deterota)")
        l("    rawvana_x_nsf = dict.fromkeys(deterota)")
        l("    rawvana_y_nsf = dict.fromkeys(deterota)")
        l("    rawvana_z_nsf = dict.fromkeys(deterota)")
        l("    rawnicr_x_sf = dict.fromkeys(deterota)")
        l("    rawnicr_y_sf = dict.fromkeys(deterota)")
        l("    rawnicr_z_sf = dict.fromkeys(deterota)")
        l("    rawnicr_x_nsf  = dict.fromkeys(deterota)")
        l("    rawnicr_y_nsf  = dict.fromkeys(deterota)")
        l("    rawnicr_z_nsf  = dict.fromkeys(deterota)")
        l("    leer_x_sf = dict.fromkeys(deterota)")
        l("    leer_y_sf = dict.fromkeys(deterota)")
        l("    leer_z_sf = dict.fromkeys(deterota)")
        l("    leer_x_nsf = dict.fromkeys(deterota)")
        l("    leer_y_nsf = dict.fromkeys(deterota)")
        l("    leer_z_nsf = dict.fromkeys(deterota)")
        l("    for wsname in dataworkspaces:")
        l("        run = mtd[wsname].getRun()")
        l("        angle = run.getProperty('deterota').value")
        l("        flipper = run.getProperty('flipper').value")
        l("        polarisation = run.getProperty('polarisation').value")
        l("        print str(angle)")
        l("        print flipper")
        l("        print polarisation")
        l("        print(str(wsname))")
        l("        if flipper == 'ON':")
        l("            if polarisation == 'x' :")
        l("                rawdata_x_sf[angle] = wsname")
        l("            elif polarisation == 'y':")
        l("                rawdata_y_sf[angle] = wsname")
        l("            elif polarisation == 'z':")
        l("                rawdata_z_sf[angle] = wsname")
        l("        else:")
        l("            if polarisation == 'x' :")
        l("                rawdata_x_nsf[angle] = wsname")
        l("            elif polarisation == 'y':")
        l("                rawdata_y_nsf[angle] = wsname")
        l("            elif polarisation == 'z':")
        l("                rawdata_z_nsf[angle] = wsname")
        l("    print rawdata_x_sf")
        l("    print rawdata_y_sf")
        l("    print rawdata_z_sf")
        l("    print rawdata_x_nsf")
        l("    print rawdata_y_nsf")
        l("    print rawdata_z_nsf")
        l("    for wsname in calibrationworkspaces:")
        l("        print('wsname = ' + str(wsname))")
        l("        run = mtd[wsname].getRun()")
        l("        wsangle = run.getProperty('deterota').value")
        l("        flipper = run.getProperty('flipper').value")
        l("        polarization = run.getProperty('polarisation')")
        l("        for key in deterota:")
        l("            if np.fabs(wsangle - key) < tol:")
        l("                angle = key")
        l("        if 'vana' in wsname:")
        l("            print('vana in wsname')")
        l("            if flipper == 'ON':")
        l("                if polarization == 'x':")
        l("                    rawvana_x_sf[angle] = wsname")
        l("                elif polarization == 'y':")
        l("                    rawvana_y_sf[angle] = wsname")
        l("                else:")
        l("                    rawvana_z_sf[angle] = wsname")
        l("            else:")
        l("                if polarization == 'x':")
        l("                    rawvana_x_nsf[angle] = wsname")
        l("                elif polarization == 'y':")
        l("                    rawvana_y_nsf[angle] = wsname")
        l("                else:")
        l("                    rawvana_z_nsf[angle] = wsname")
        l("        if 'nicr' in wsname:")
        l("            if flipper == 'ON':")
        l("                if polarization == 'x':")
        l("                    rawnicr_x_sf[angle] = wsname")
        l("                elif polarization == 'y':")
        l("                    rawnicr_y_sf[angle] = wsname")
        l("                else:")
        l("                    rawnicr_z_sf[angle] = wsname")
        l("            else:")
        l("                if polarization == 'x':")
        l("                    rawnicr_x_nsf[angle] = wsname")
        l("                elif polarization == 'y':")
        l("                    rawnicr_y_nsf[angle] = wsname")
        l("                else:")
        l("                    rawnicr_z_nsf[angle] = wsname")
        l("        if 'leer' in wsname:")
        l("            if flipper == 'ON':")
        l("                if polarization == 'x':")
        l("                    leer_x_sf[angle] = wsname")
        l("                elif polarization == 'y':")
        l("                    leer_y_sf[angle] = wsname")
        l("                else:")
        l("                    leer_z_sf[angle] = wsname")
        l("            else:")
        l("                if polarization == 'x':")
        l("                    leer_x_nsf[angle] = wsname")
        l("                elif polarization == 'y':")
        l("                    leer_y_nsf[angle] = wsname")
        l("                else:")
        l("                    leer_z_nsf[angle] = wsname")
        l()
        l("    logger.debug('raw data x flip: '+str(rawdata_x_sf)+'\\n'+'raw data y flip: '+str(rawdata_y_sf))")
        l("    logger.debug('raw data z flip: '+str(rawdata_z_sf)+'\\n'+'raw data x nflip: '+str(rawdata_x_nsf))")
        l("    logger.debug('raw data y nflip: '+str(rawdata_y_nsf)+'\\n'+'raw data z nflip: '+str(rawdata_z_nsf))")
        l("    logger.debug('vana x flip: '+str(rawvana_x_sf)+'\\n'+'vana y flip: '+str(rawvana_y_sf))")
        l("    logger.debug('vana z flip: '+str(rawvana_z_sf)+'\\n'+'vana x nflip: '+str(rawvana_x_nsf))")
        l("    logger.debug('vana y nflip: '+str(rawvana_y_nsf)+'\\n'+'vana z nflip: '+str(rawvana_z_nsf))")
        l("    logger.debug('nicr x flip: '+str(rawnicr_x_sf)+'\\n'+'nicr y flip: '+str(rawnicr_y_sf))")
        l("    logger.debug('nicr z flip: '+str(rawnicr_z_sf)+'\\n'+'nicr x nflip: '+str(rawnicr_x_nsf))")
        l("    logger.debug('nicr y nflip: '+str(rawnicr_y_nsf)+'\\n'+'nicr z nflip: '+str(rawnicr_z_nsf))")
        l("    logger.debug('leer x flip: '+str(leer_x_sf)+'\\n'+'leer y flip: '+str(leer_y_sf))")
        l("    logger.debug('leer z flip: '+str(leer_z_sf)+'\\n'+'leer x nflip: '+str(leer_x_nsf))")
        l("    logger.debug('leer y nfip: '+str(leer_y_nsf)+'\\n'+'leer z nflip:'+str(leer_z_nsf))")
        l("    group_names = [out_ws + '_rawdata_x_sf', out_ws + '_rawdata_y_sf', out_ws + '_rawdata_z_sf', out_ws + "
          "'_rawdata_x_nsf', out_ws + '_rawdata_y_nsf', out_ws + '_rawdata_z_nsf', out_ws + '_rawvana_x_sf', out_ws + "
          "'_rawvana_y_sf', out_ws + '_rawvana_z_sf', out_ws + '_rawvana_x_nsf', out_ws + '_rawvana_y_nsf', out_ws + "
          "'_rawvana_z_nsf', out_ws + '_rawnicr_x_sf', out_ws + '_rawnicr_y_sf', out_ws + '_rawnicr_z_sf', out_ws + "
          "'_rawnicr_x_nsf', out_ws + '_rawnicr_y_nsf', out_ws + '_rawnicr_z_nsf', out_ws + '_leer_x_sf', out_ws + "
          "'_leer_y_sf', out_ws + '_leer_z_sf', out_ws + '_leer_x_nsf', out_ws + '_leer_y_nsf', out_ws + '_leer_z_nsf']")
        l()
        l("    print str(group_names)")
        l("    remove_ws_name = out_ws + '_'")
        l("    for var in group_names:")
        l("        ws = eval(var.split(remove_ws_name)[1]).values()")
        l("        print(str(ws))")"""
        """l("        if None in ws:")
        l("            msg = 'Group ' + var + ' has no data for some of detector positions. "
          "Try to increase 2theta tolerance'")
        l("            logger.error(msg + ' Values: ' + str(eval(var.split(remove_ws_name)[1])))")
        l("            raise RuntimeError(msg)")"""
        """l("    print (str(dataworkspaces))")
        l("    for var in group_names:")
        l("        gname = var + '_group'")
        l("        print(gname)")
        l("        ws = eval(var.split(remove_ws_name)[1]).values()")
        l("        print(ws)")
        l("        if not None in ws:")
        l("            GroupWorkspaces(ws, OutputWorkspace=gname)")
        l("    print(out_ws)")"""
        """l("    for var in group_names:")
        l("        gname = var + '_group'")
        l("        extract_norm_workspace(mtd[gname])")
        l("        print 'first merge and normalize'")
        l("        merge_and_normalize(gname)")"""
        l()
        """l("    for var in ['rawdata_x', 'rawdata_y', 'rawdata_z', 'rawvana_x', 'rawvana_y', 'rawvana_z',
         'rawnicr_x', 'rawnicr_y',  'rawnicr_z']:")
        l("        data_wname_sf = out_ws + '_' + var + '_sf' + '_group'")
        l("        data_wname_nsf = out_ws + '_' + var + '_nsf' + '_group'")
        l("        norm_ratio_sf = Divide(data_wname_sf + '_norm', out_ws + '_leer_sf_group_norm', "
          "OutputWorkspace=out_ws + var + '_sf' + '_nratio')")
        l("        norm_ratio_nsf = Divide(data_wname_nsf + '_norm', out_ws + '_leer_nsf_group_norm',"
          "OutputWorkspace=out_ws + var + '_nsf' + '_nratio')")
        l("        sfleer_scaled = Multiply(out_ws + '_leer_sf_group', norm_ratio_sf, "
          "OutputWorkspace=out_ws + '_leer_sf_' + var)")
        l("        print str(data_wname_nsf + '_norm'), str(out_ws + '_leer_nsf_group_norm')")
        l("        nsfleer_scaled = Multiply(out_ws + '_leer_nsf_group', norm_ratio_nsf, "
          "OutputWorkspace=out_ws + '_leer_nsf_' + var)")
        l()
        l("        Minus(data_wname_sf, sfleer_scaled, OutputWorkspace=out_ws + '_sf' + var[3:] + '_group')")
        l("        CloneWorkspace(data_wname_sf + '_norm', "
          "OutputWorkspace=out_ws + '_sf' + var[3:] + '_group_norm')")
        l("        Minus(data_wname_nsf, nsfleer_scaled, OutputWorkspace=out_ws + '_nsf' + var[3:] + '_group')")
        l("        CloneWorkspace(data_wname_nsf + '_norm', "
          "OutputWorkspace=out_ws + '_nsf' + var[3:] + '_group_norm')")
        l()
        l("        print 'second merge and normalized'")
        l("        merge_and_normalize(out_ws + var[3:] + '_sf' + '_group')")
        l("        merge_and_normalize(out_ws + var[3:] + + '_nsf' '_group')")
        l()
        l("    vana_sf_nsf_sum = Plus(out_ws + '_sfvana_group', out_ws + '_nsfvana_group')")
        l("    vana_sf_nsf_sum_norm = Plus(out_ws + '_sfvana_group_norm', out_ws + '_nsfvana_group_norm')")
        l()
        l("    vana_total = SumSpectra(vana_sf_nsf_sum)")
        l("    vana_total_norm = SumSpectra(vana_sf_nsf_sum_norm)")
        l()
        l("    vana_mean = Mean(', '.join(vana_total.getNames()))")
        l("    vana_mean_norm = Mean(', '.join(vana_total_norm.getNames()))")
        l("    vana_coefs = vana_sf_nsf_sum/vana_mean")
        l("    vana_coefs_norm = vana_sf_nsf_sum_norm/vana_mean_norm")
        l()
        l("    vana_coefs_total = vana_coefs/vana_coefs_norm")
        l()
        l("    for x in xax:")
        l("        sfdata_norm = Multiply(out_ws + '_sfdata_group_norm', vana_coefs_total, "
          "OutputWorkspace=out_ws + '_sfdata_vcorr_norm' + '_' + x)")
        l("        nsfdata_norm = Multiply(out_ws + '_nsfdata_group_norm', vana_coefs_total, "
          "OutputWorkspace=out_ws + '_nsfdata_vcorr_norm' + '_' + x)")
        l("    for x in xax:")
        l("        print 'sfdata_merged' + x")
        l("        sfdata_merged = DNSMergeRuns(out_ws + '_sfdata_group', x, "
          "OutputWorkspace=out_ws + '_sfdata_group_m0' + '_' + x)")
        l("        print 'nsfdata_merged' + x")
        l("        nsfdata_merged = DNSMergeRuns(out_ws + '_nsfdata_group', x, "
          "OutputWorkspace=out_ws + '_nsfdata_group_m0' + '_' + x)")
        l("        print 'sfnorm_merged' + x")
        l("        sfnorm_merged = DNSMergeRuns(out_ws + '_sfdata_vcorr_norm' + '_' + x, x,"
          "OutputWorkspace=out_ws + '_sfdata_vcorr_norm_m' + '_' + x)")
        l("        print 'msfnorm_merged' + x")
        l("        nsfnorm_merged = DNSMergeRuns(out_ws + '_nsfdata_vcorr_norm' + '_' + x, x,"
          "OutputWorkspace=out_ws + '_nsfdata_vcorr_norm_m' + '_' + x )")
        l("        Divide(sfdata_merged, sfnorm_merged, OutputWorkspace=out_ws + '_sfdata_vcorr_m' + '_' + x)")
        l("        Divide(nsfdata_merged, nsfnorm_merged, OutputWorkspace=out_ws + '_nsfdata_vcorr_m' + '_' + x)")
        l()
        l("    nicr_nratio = Divide(out_ws + '_nsfnicr_group_norm', out_ws + '_sfnicr_group_norm', "
          "OutputWorkspace=out_ws + '_nsfnicr_nratio')")
        l("    nicr_coefs_norm = Multiply(out_ws + '_sfnicr_group', nicr_nratio, "
          "OutputWorkspace=out_ws + '_sfnicr_scaled')")
        l("    nicr_coefs = Minus(out_ws + '_nsfnicr_group', nicr_coefs_norm)")
        l("    nicr_coefs_normalized = nicr_coefs/nicr_coefs_norm")
        l("    yunit = nicr_coefs.getItem(0).YUnit()")
        l("    data_nratio = nsfdata_norm/sfdata_norm")
        l("    sfdata_scaled = Multiply(out_ws + '_sfdata_group', data_nratio, "
          "OutputWorkspace=out_ws + '_sfdata_group_scaled')")
        l("    nicr_corr_step1 = Minus(out_ws + '_nsfdata_group', sfdata_scaled)")
        l("    nicr_corr_step2 = nicr_corr_step1/nicr_coefs_normalized")
        l("    for i in range(nicr_corr_step2.getNumberOfEntries()):")
        l("        nicr_corr_step2.getItem(i).setYUnit(yunit)")
        l("    for x in xax:")
        l("        nsfdata_fcorr = Plus(out_ws + '_nsfdata_group', nicr_corr_step2, "
          "OutputWorkspace=out_ws + '_nsfdata_fcorr' + '_' + x)")
        l("        nsfdata_fcorr_norm = CloneWorkspace(out_ws + '_nsfdata_vcorr_norm' + '_' + x, "
          "OutputWorkspace = out_ws + '_nsfdata_fcorr_norm' + '_' + x)")
        l("        sfdata_fcorr = Minus(out_ws + '_sfdata_group', nicr_corr_step2, "
          "OutputWorkspace=out_ws + '_sfdata_fcorr' + '_' + x)")
        l("        sfdata_fcorr_norm = CloneWorkspace(out_ws + '_sfdata_vcorr_norm' + '_' + x, "
          "OutputWorkspace = out_ws + '_sfdata_fcorr_norm' + '_' + x)")
        l("        merge_and_normalize(out_ws + '_sfdata_fcorr', '_' + x)")
        l("        merge_and_normalize(out_ws + '_nsfdata_fcorr', '_' + x)")
        l()
        l("        spin_incoh = Scale(out_ws + '_sfdata_fcorr_m' + '_' + x, Factor=1.5, Operation='Multiply', "
          "OutputWorkspace = out_ws + '_spin_incoh' + '_' + x)")
        l("        step1 = 0.5*sfdata_fcorr*data_nratio")
        l("        coh_group = nsfdata_fcorr-step1")
        l("        print 'nuclear_coh_merged'")
        l("        nuclear_coh_merged = DNSMergeRuns('coh_group', x)")
        l("        nuclear_coh = Divide(nuclear_coh_merged, out_ws + '_nsfdata_fcorr_norm_m' + '_' + x, "
          "OutputWorkspace=out_ws + '_nuclear_coherent' + '_' + x)")
        l("        outws = Divide(nuclear_coh, spin_incoh, OutputWorkspace=out_ws+ '_' + x)")
        l("        outws = Divide(nuclear_coh, spin_incoh, OutputWorkspace=out_ws+ '_' + x)")
        """



        print(str(script[0]))

        return script[0]


class DNSReductionScripter(BaseReductionScripter):

    def __init__(self, name, facility):
        BaseReductionScripter.__init__(self, name, facility)
