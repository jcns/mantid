import xml.dom.minidom

import os
import re

from reduction_gui.reduction.scripter import BaseScriptElement, BaseReductionScripter

import mantid.simpleapi as api


class DNSScriptElement(BaseScriptElement):
    """
    script element of the dns reduction ui
    """

    # save to file
    DEF_SaveToFile = False

    # normalization
    NORM_TIME    = 0
    NORM_MONITOR = 1

    # default values

    # data reduction settings
    DEF_DetEffi     = True
    DEF_SumVan      = False
    DEF_SubInst     = True
    DEF_SubFac      = 1.0
    DEF_FlipRatio  = True
    DEF_FlipFac    = 1.0
    DEF_MultiSF     = 0.0
    DEF_Normalise   = NORM_TIME
    DEF_NeutWaveLen = 0.0
    #DEF_Intermediate = False

    # sample
    OUT_POLY_AMOR    = 0
    OUT_SINGLE_CRYST = 1
    DEF_Output       = OUT_POLY_AMOR

    # separation
    SEP_XYZ = 0
    SEP_COH = 1
    SEP_NO  = 2

    # parameters for polycrystal/amorphous
    DEF_OutAxisQ      = True
    DEF_OutAxisD      = True
    DEF_OutAxis2Theta = True
    DEF_Separation    = SEP_XYZ

    # parameters for single crystal reduction
    DEF_OmegaOffset  = 0.0
    DEF_LatticeA     = 0.0
    DEF_LatticeB     = 0.0
    DEF_LatticeC     = 0.0
    DEF_LatticeAlpha = 0.0
    DEF_LatticeBeta  = 0.0
    DEF_LatticeGamma = 0.0
    DEF_ScatterU1    = 0.0
    DEF_ScatterU2    = 0.0
    DEF_ScatterU3    = 0.0
    DEF_ScatterV1    = 0.0
    DEF_ScatterV2    = 0.0
    DEF_ScatterV3    = 0.0

    XML_TAG = "DNSReduction"

    def __init__(self):
        BaseScriptElement.__init__(self)

        # facility and instrument name
        self.facility_name   = ""
        self.instrument_name = ""

        # sample data parameters
        self.sampleDataPath = ""
        self.filePrefix     = ""
        self.fileSuffix     = ""

        # runs of sample data
        self.dataRuns = []

        # angles of detectors to be mask
        self.maskAngles = []

        # save data to file
        self.saveToFile = self.DEF_SaveToFile
        self.outDir     = ""
        self.outPrefix  = ""

        # path to standard data directory
        self.standardDataPath = ""

        # reduction settings
        self.detEffi        = self.DEF_DetEffi
        self.sumVan         = self.DEF_SumVan
        self.subInst        = self.DEF_SubInst
        self.subFac         = self.DEF_SubFac
        self.flipRatio     = self.DEF_FlipRatio
        self.flipFac       = self.DEF_FlipFac
        self.multiSF        = self.DEF_MultiSF
        self.normalise      = self.DEF_Normalise
        self.neutronWaveLen = self.DEF_NeutWaveLen

        # sample parameter type
        self.out = self.DEF_Output

        # parameters for polycrystal/amorph
        self.outAxisQ      = self.DEF_OutAxisQ
        self.outAxisD      = self.DEF_OutAxisD
        self.outAxis2Theta = self.DEF_OutAxis2Theta
        self.separation    = self.DEF_Separation

        # parameters for single crystal
        self.omegaOffset  = self.DEF_OmegaOffset
        self.latticeA     = self.DEF_LatticeA
        self.latticeB     = self.DEF_LatticeB
        self.latticeC     = self.DEF_LatticeC
        self.latticeAlpha = self.DEF_LatticeAlpha
        self.latticeBeta  = self.DEF_LatticeBeta
        self.latticeGamma = self.DEF_LatticeGamma
        self.scatterU1    = self.DEF_ScatterU1
        self.scatterU2    = self.DEF_ScatterU2
        self.scatterU3    = self.DEF_ScatterU3
        self.scatterV1    = self.DEF_ScatterV1
        self.scatterV2    = self.DEF_ScatterV2
        self.scatterV3    = self.DEF_ScatterV3

        tmp = api.LoadEmptyInstrument(InstrumentName="DNS")
        instrument = tmp.getInstrument()
        api.DeleteWorkspace(tmp)

        self.suff_norm = instrument.getStringParameter("normws_suffix")[0]

    def reset(self):
        """
        Declare variables to reset the view
        """

        self.facility_name   = ""
        self.instrument_name = ""

        self.sampleDataPath = ""
        self.filePrefix     = ""
        self.fileSuffix     = ""

        self.dataRuns = []

        self.maskAngles = []

        self.saveToFile = self.DEF_SaveToFile
        self.outDir     = ""
        self.outPrefix  = ""

        self.standardDataPath = ""

        self.detEffi        = self.DEF_DetEffi
        self.sumVan         = self.DEF_SumVan
        self.subInst        = self.DEF_SubInst
        self.subFac         = self.DEF_SubFac
        self.flipRatio     = self.DEF_FlipRatio
        self.flipFac       = self.DEF_FlipFac
        self.multiSF        = self.DEF_MultiSF
        self.normalise      = self.DEF_Normalise
        self.neutronWaveLen = self.DEF_NeutWaveLen

        self.out = self.DEF_Output

        self.outAxisQ      = self.DEF_OutAxisQ
        self.outAxisD      = self.DEF_OutAxisD
        self.outAxis2Theta = self.DEF_OutAxis2Theta
        self.separation    = self.DEF_Separation

        self.omegaOffset  = self.DEF_OmegaOffset
        self.latticeA     = self.DEF_LatticeA
        self.latticeB     = self.DEF_LatticeB
        self.latticeC     = self.DEF_LatticeC
        self.latticeAlpha = self.DEF_LatticeAlpha
        self.latticeBeta  = self.DEF_LatticeBeta
        self.latticeGamma = self.DEF_LatticeGamma
        self.scatterU1    = self.DEF_ScatterU1
        self.scatterU2    = self.DEF_ScatterU2
        self.scatterU3    = self.DEF_ScatterU3
        self.scatterV1    = self.DEF_ScatterV1
        self.scatterV2    = self.DEF_ScatterV2
        self.scatterV3    = self.DEF_ScatterV3

    def to_xml(self):
        """
        save the input from the view to an XML file
        :return: XML File with all elements
        """

        res = [""]

        def put(tag, val):
            """
            put element to XML file
            :param tag: tag of the element
            :param val: value of the element
            """
            res[0] += " <{0}>{1}</{0}>\n".format(tag, str(val))

        put("sample_data_path", self.sampleDataPath)
        put("file_prefix",      self.filePrefix)
        put("file_suffix",      self.fileSuffix)

        for (runs, ws, cmnt) in self.dataRuns:
            put("data_runs",             runs)
            put("data_output_workspace", ws)
            put("data_comment",          cmnt)

        for (min, max) in self.maskAngles:
            put("mask_min_Angle", min)
            put("mask_max_Angle", max)

        put("save_to_file",       self.saveToFile)
        put("output_directory",   self.outDir)
        put("output_file_prefix", self.outPrefix)

        put("standard_data_path", self.standardDataPath)

        put("detector_efficiency",        self.detEffi)
        put("sum_Vanadium",               self.sumVan)
        put("subtract_instrument",        self.subInst)
        put("subtract_instrument_factor", self.subFac)
        put("flipping_ratio", self.flipRatio)
        put("flipping_ratio_factor", self.flipFac)
        put("multiple_SF_scattering",     self.multiSF)
        put("normalise",                  self.normalise)
        put("neutron_wave_length",        self.neutronWaveLen)

        put("output", self.out)

        put("output_Axis_q",      self.outAxisQ)
        put("output_Axis_d",      self.outAxisD)
        put("output_Axis_2Theta", self.outAxis2Theta)
        put("separation",         self.separation)

        put("omega_offset",             self.omegaOffset)
        put("lattice_parameters_a",     self.latticeA)
        put("lattice_parameters_b",     self.latticeB)
        put("lattice_parameters_c",     self.latticeC)
        put("lattice_parameters_alpha", self.latticeAlpha)
        put("lattice_parameters_beta",  self.latticeBeta)
        put("lattice_parameters_gamma", self.latticeGamma)
        put("scattering_Plane_u_1",     self.scatterU1)
        put("scattering_Plane_u_2",     self.scatterU2)
        put("scattering_Plane_u_3",     self.scatterU3)
        put("scattering_Plane_v_1",     self.scatterV1)
        put("scattering_Plane_v_2",     self.scatterV2)
        put("scattering_Plane_v_3",     self.scatterV3)

        return "<{0}>\n{1}</{0}>\n".format(self.XML_TAG, res[0])

    def from_xml(self, xmlStr):
        """
        read data from the XML file
        :param xmlStr: string from XML file
        """

        self.reset()

        dom = xml.dom.minidom.parseString(xmlStr)
        els = dom.getElementsByTagName(self.XML_TAG)

        if els:

            dom = els[0]

            def get_str(tag, default=""):
                """
                get string element from XML file
                :param tag: tag of the elements
                :param default: default value of the element
                :return: value of the element
                """
                return BaseScriptElement.getStringElement(dom, tag, default=default)

            def get_int(tag, default):
                """
                get integer element from XML file
                :param tag: tag of the element
                :param default: default value of the element
                :return: value of the element
                """
                return BaseScriptElement.getIntElement(dom, tag, default=default)

            def get_flt(tag, default):
                """
                get float element from XML file
                :param tag: tag of the element
                :param default: default value of the element
                :return: value of the element
                """
                return BaseScriptElement.getFloatElement(dom, tag, default=default)

            def get_str_lst(tag):
                """
                get string list element form XML file
                :param tag: tag of the element
                :return: value of the element
                """
                return BaseScriptElement.getStringList(dom, tag)

            def get_bol(tag, default):
                """
                get boolean element from XML file
                :param tag: tag of the element
                :param default: default value of the element
                :return: value of the element
                """
                return BaseScriptElement.getBoolElement(dom, tag, default=default)

            self.sampleDataPath = get_str("sample_data_path")
            self.filePrefix     = get_str("file_prefix")
            self.fileSuffix     = get_str("file_suffix")
            data_runs           = get_str_lst("data_runs")
            data_out_ws         = get_str_lst("data_output_workspace")
            data_comments       = get_str_lst("data_comment")

            for i in range(min(len(data_runs), len(data_out_ws), len(data_comments))):
                self.dataRuns.append((data_runs[i], data_out_ws[i], data_comments[i]))

            mask_min = get_str_lst("mask_min_Angle")
            mask_max = get_str_lst("mask_max_Angle")

            for i in range(min(len(mask_min), len(mask_max))):
                self.maskAngles.append((mask_min[i], mask_max[i]))

            self.saveToFile = get_bol("save_to_file", self.DEF_SaveToFile)
            self.outDir     = get_str("output_directory")
            self.outPrefix  = get_str("output_file_prefix")

            self.standardDataPath = get_str("standard_data_path")

            self.detEffi        = get_bol("detector_efficiency",        self.DEF_DetEffi)
            self.sumVan         = get_bol("sum_Vanadium",               self.DEF_SumVan)
            self.subInst        = get_bol("subtract_instrument",        self.DEF_SubInst)
            self.subFac         = get_flt("subtract_instrument_factor", self.subFac)
            self.flipRatio     = get_bol("flipping_ratio", self.DEF_FlipRatio)
            self.multiSF        = get_flt("multiple_SF_scattering",     self.DEF_MultiSF)
            self.normalise      = get_int("normalise",                  self.DEF_Normalise)
            self.neutronWaveLen = get_flt("neutron_wave_length",        self.DEF_NeutWaveLen)

            self.out = get_int("output", self.DEF_Output)

            self.outAxisQ      = get_bol("output_Axis_q",      self.DEF_OutAxisQ)
            self.outAxisD      = get_bol("output_Axis_d",      self.DEF_OutAxisD)
            self.outAxis2Theta = get_bol("output_Axis_2Theta", self.DEF_OutAxis2Theta)
            self.separation    = get_int("separation",         self.DEF_Separation)

            self.omegaOffset  = get_flt("omega_offset",             self.omegaOffset)
            self.latticeA     = get_flt("lattice_parameters_a",     self.DEF_LatticeA)
            self.latticeB     = get_flt("lattice_parameters_b",     self.DEF_LatticeB)
            self.latticeC     = get_flt("lattice_parameters_c",     self.DEF_LatticeC)
            self.latticeAlpha = get_flt("lattice_parameters_alpha", self.DEF_LatticeAlpha)
            self.latticeBeta  = get_flt("lattice_parameters_beta",  self.DEF_LatticeBeta)
            self.latticeGamma = get_flt("lattice_parameters_gamma", self.DEF_LatticeGamma)
            self.scatterU1    = get_flt("scattering_Plane_u_1",     self.DEF_ScatterU1)
            self.scatterU2    = get_flt("scattering_Plane_u_2",     self.DEF_ScatterU2)
            self.scatterU3    = get_flt("scattering_Plane_u_3",     self.DEF_ScatterU3)
            self.scatterV1    = get_flt("scattering_Plane_v_1",     self.DEF_ScatterV1)
            self.scatterV2    = get_flt("scattering_Plane_v_2",     self.DEF_ScatterV2)
            self.scatterV3    = get_flt("scattering_Plane_v_3",     self.DEF_ScatterV3)

    def error(self, message):
        """
        :param message: error message
        :raises RuntimeError: error in ui for DNS reduction
        """
        raise RuntimeError("DNS reduction error: "+message)

    def _test_parameters(self):
        """
        test parameters from the ui
        :raise RuntimeError: if state is not proper for reduction
        """

        # path to sample data must exist
        if not os.path.lexists(self.sampleDataPath):
            self.error("sample data path not found")

        # need prefix and suffix to find sample data
        if not self.filePrefix:
            self.error("missing sample data file prefix")

        if not self.fileSuffix:
            self.error("missing sample data file suffix")

        # there must be data in the first row of the run data table
        (first_runs, first_workspace, first_comment) = self.dataRuns[0]
        if not self.dataRuns:
            self.error("Missing sample data runs")
        elif not first_runs and not first_workspace and not first_comment:
            self.error("First line empty")

        # the must be a run in every row and a workspace name for every run
        for (runs, workspace, comment) in self.dataRuns:
            if not runs:
                self.error("All rows must contain run numbers")
            elif runs and not workspace:
                self.error("There must be a workspace to all run numbers")

        # test for mask detectors table
        self._test_mask_angles()

        # if data should be saved to file output directory must be writeable and prefix must be given
        if self.saveToFile:
            if not os.path.lexists(self.outDir):
                self.error("output directory not found")
            elif not os.access(self.outDir, os.W_OK):
                self.error("cant write in directory "+str(self.outDir))

            if not self.outPrefix:
                self.error("missing output file prefix")

        #  path to standard data must exist
        if not os.path.lexists(self.standardDataPath):
            self.error("standard data path not found")
        else:
            # test for standard data files
            self._standard_data_files()

        # there must be at least selected one unit for x axis of the output workspace
        if self.out == self.OUT_POLY_AMOR and not self.outAxisQ and not self.outAxisD and not self.outAxis2Theta:
            self.error("no abscissa selected")

        # one angle of the lattice parameters angles cant be bigger than the other two added and
        # the scatter parameters can't all be zero
        if self.out == self.OUT_SINGLE_CRYST:
            if self.latticeAlpha > self.latticeBeta + self.latticeBeta or \
                            self.latticeBeta > self.latticeAlpha + self.latticeGamma or \
                            self.latticeGamma > self.latticeAlpha + self.latticeBeta:
                self.error("Invalid lattice angles: one angle can't be bigger than the other to added")
            if self.scatterU1 == 0.0 and self.scatterU2 == 0.0 and self.scatterU3 == 0.0:
                self.error("|B.u|~0")
            if self.scatterV1 == 0.0 and self.scatterV2 == 0.0 and self.scatterV3 == 0.0:
                self.error("|B.v|~0")

    def _test_mask_angles(self):
        """
        test the angles of mask detector table
        """
        for i in range(len(self.maskAngles)):
            (min_angle, max_angle) = self.maskAngles[i]

            # set min or max angle if an angle is missing
            if not max_angle:
                max_angle = 180.0
            elif not min_angle:
                min_angle = 0.0
            self.maskAngles[i] = (min_angle, max_angle)

            # angles must be bigger than 0.0 and lower than 180
            if float(min_angle) < 0.0 or float(min_angle) > 180.0:
                error_message = "Angle must be between 0.0 and 180.0 (error in row "+str(i+1)+" min angle)"
                self.error(error_message)

            if float(max_angle) < 0.0 or float(max_angle) > 180.0:
                error_message = "Angle must be between 0.0 and 180.0 (error in row "+str(i+1)+" max angle)"
                self.error(error_message)

            # all min angle must be lower than max angle
            if not float(min_angle) < float(max_angle):
                error_message = "Min Angle must be smaller than max Angle (error in row "+str(i+1)+")"
                self.error(error_message)

    def _standard_data_files(self):
        """
        test if there is at least one file of the standard data needed for reduction 
        """
        tmp = api.LoadEmptyInstrument(InstrumentName="DNS")
        instrument = tmp.getInstrument()
        api.DeleteWorkspace(tmp)

        if self.detEffi:
            det_eff_filename = instrument.getStringParameter("vana")[0]
            found = self._search_std_data_file(self.standardDataPath, det_eff_filename)
            if not found:
                self.error("no file for detector efficiency correction in "+str(self.standardDataPath)+" found")
        if self.subInst or self.detEffi or self.flipRatio:
            sub_inst_filename = instrument.getStringParameter("bkg")[0]
            found = self._search_std_data_file(self.standardDataPath, sub_inst_filename)
            if not found:
                self.error("no file to subtract of instrument background for sample in "+str(self.standardDataPath)
                           + " found")
        if self.flipRatio:
            flip_ratio_filename = instrument.getStringParameter("nicr")[0]
            found = self._search_std_data_file(self.standardDataPath, flip_ratio_filename)
            if not found:
                self.error("no file for flipping ratio correction in "+ str(self.standardDataPath)+" found")

    def _search_std_data_file(self, path, name):
        """
        searching for a file with a filename that contains name
        :param path: path to the directory where the file should be
        :param name: string that must be in a file
        :return: true if there is a file which name contains 
        """
        files = os.listdir(path)
        for f in files:
            if f.__contains__(name):
                return True
        return False

    def _search_fs(self, path, prefix, suffix, run_numbers):
        """
        search for all sample files,error if there is no file with this run number, prefix and suffix in the path
        :param path: path of sample files
        :param prefix: prefix of sample files
        :param suffix: suffix of sample files
        :param run_numbers: run numbers of the sample files
        :return: list of the sample files
        """
        numbers = run_numbers.split(",")
        fs      = []

        found = False

        for run_number in numbers:
            if run_number.__contains__(":"):
                (start, stop) = run_number.split(":")
                start = int(start)
                stop = int(stop)
                for i in range(start, stop+1):
                    for f in os.listdir(path):
                        if re.match(r"{}0*{}{}.d_dat$".format(prefix, int(i), suffix), f):
                            found = True
                            fs.append(str(f))
                    if not found:
                        self.error("file with prefix "+prefix+", run number "+str(i)+" and suffix "+suffix+" not found")
                    found = False
            else:
                for f in os.listdir(path):
                    if re.match(r"{}0*{}{}.d_dat".format(prefix, int(run_number), suffix), f):
                        found = True
                        fs.append(str(f))
                if not found:
                    self.error("file with prefix "+prefix+", run number "+str(run_number)+" and suffix "+suffix
                               + " not found")
                found = False

        return fs

    def _parameter_dict(self):
        """
        create a dictionary with all parameters for the reduction
        :return: parameter dictionary
        """

        parameters = {}

        sample_data = {"Data path": self.sampleDataPath, "File prefix": self.filePrefix, "File suffix": self.fileSuffix}

        workspaces = []
        files      = []
        comments   = []

        for i in range(len(self.dataRuns)):
            (run_number, out_ws, comment) = self.dataRuns[i]
            workspaces.append(str(out_ws))
            files.append(self._search_fs(self.sampleDataPath, self.filePrefix, self.fileSuffix, run_number))
            comments.append(str(comment))

        sample_data["Data Table workspaces"] = workspaces
        sample_data["Data Table files"]      = files
        sample_data["Data Table comments"]   = comments

        parameters["Sample Data"] = sample_data

        parameters["Mask Detectors angles"] = self.maskAngles

        save_to_file = {"Save boolean": str(self.saveToFile), "Output directory": self.outDir,
                        "Output file prefix": self.outPrefix}

        parameters["Save"] = save_to_file

        std_data = {"Path": self.standardDataPath}

        parameters["Standard Data"] = std_data

        data_red_settings = {"Detector efficiency correction": str(self.detEffi),
                             "Sum Vanadium over detector position": str(self.sumVan),
                             "Subtract instrument background": str(self.subInst), "Subtract factor": self.subFac,
                             "Fliping ratio correction": str(self.flipRatio), "Fliping ratio factor": self.flipFac,
                             "Multiple SF scattering probability": self.multiSF,
                             "Neutron wavelength": self.neutronWaveLen}

        if self.normalise == self.NORM_MONITOR:
            norm = "monitor"
        else:
            norm = "time"

        data_red_settings["Normalization"] = norm

        parameters["Data reduction settings"] = data_red_settings

        type = dict()

        if self.out == self.OUT_POLY_AMOR:
            type["Type"] = "Polycrystal/Amorphous"

            out_ax = []
            if self.outAxisD:
                out_ax.append("d-Spacing")
            if self.outAxisQ:
                out_ax.append("|Q|")
            if self.outAxis2Theta:
                out_ax.append("2theta")

            type["Abscissa"] = str(out_ax)

            if self.separation == self.SEP_XYZ:
                type["Separation"] = "XYZ"
            elif self.separation == self.SEP_COH:
                type["Separation"] = "Coherent/Incoherent"
            else:
                type["Separation"] = "No"

        if self.out == self.OUT_SINGLE_CRYST:
            type["Type"] = "Single Crystal"

            type["Omega offset"] = self.omegaOffset

            lattice = dict()
            lattice["a"] = self.latticeA
            lattice["b"] = self.latticeB
            lattice["c"] = self.latticeC

            lattice["alpha"] = self.latticeAlpha
            lattice["beta"]  = self.latticeBeta
            lattice["gamma"] = self.latticeGamma

            type["Lattice parameters"] = lattice

            scatter = {}
            u = "{}, {}, {}".format(self.scatterU1, self.scatterU2, self.scatterU3)
            v = "{}, {}, {}".format(self.scatterV1, self.scatterV2, self.scatterV3)

            scatter["u"] = u
            scatter["v"] = v

            type["Scattering Plane"] = scatter

        parameters["Sample"] = type

        return parameters

    def to_script(self):
        """
        create a python script for dns reduction
        :return: script
        """

        self._test_parameters()

        parameters = self._parameter_dict()

        # generated script
        script = [""]

        def l(line=""):
            """
            add line to the script
            :param line: text for the new line
            """
            script[0] += line+"\n"

        l("import numpy as np")
        l("import os")
        l()
        l("config['default.facility'] = '{}'".format(self.facility_name))
        l("config['default.instrument'] = '{}'".format(self.instrument_name))
        l()
        # path to sample data files
        l("data_path  = '{}'".format(parameters["Sample Data"]["Data path"]))
        # lists of files, workspaces and comments
        l("files      = {}".format(parameters["Sample Data"]["Data Table files"]))
        l("workspaces = {}".format(parameters["Sample Data"]["Data Table workspaces"]))
        l("comments   = {}".format(parameters["Sample Data"]["Data Table comments"]))
        l()
        # list of angles for mask detectors
        l("maskAngles    = {}".format(parameters["Mask Detectors angles"]))
        l("maskAngles    = [str(angle) for angle in maskAngles]")
        l("maskAnglesStr = '; '.join(maskAngles)")
        l()
        # parameters for save to file
        l("saveToFile    = {}".format(parameters["Save"]["Save boolean"]))
        l("filePrefix    = '{}'".format(parameters["Save"]["Output file prefix"]))
        l("fileDirectory = '{}'".format(parameters["Save"]["Output directory"]))
        l()
        # standard data path
        l("std_path = '{}'".format(parameters["Standard Data"]["Path"]))
        l()
        # data reduction settings
        l("fliper_bool = {}".format(parameters["Data reduction settings"]["Fliping ratio correction"]))
        l("flipFac     = '{}'".format(parameters["Data reduction settings"]["Fliping ratio factor"]))
        l("detEffi      = {}".format(self.detEffi))
        l("flipRatio   = {}".format(self.flipRatio))
        l("subInst      = {}".format(self.subInst))
        l()
        l("if subInst:")
        l("    subInstFac = '{}'".format(parameters["Data reduction settings"]["Subtract factor"]))
        l("else:")
        l("    subInstFac = ''")
        l()
        l("norm = '{}'".format(parameters["Data reduction settings"]["Normalization"]))
        l("wavelength = '{}'".format(parameters["Data reduction settings"]["Neutron wavelength"]))
        l()
        # list of x data for changed wavelength
        l("if float(wavelength):")
        l("    dataX = np.zeros(2)")
        l("    dataX.fill(float(wavelength) + 0.00001)")
        l("    dataX[::2] -= 0.000002")
        l("else:")
        l("    dataX = []")
        l("dataX     = [str(x) for x in dataX]")
        l("dataX_str = ', '.join(dataX)")
        l()
        # sample data parameters
        l("parametersSample = {}".format(dict(parameters["Sample"])))
        l()
        # list of output workspaces x axis units
        l("if parametersSample['Type'] == 'Polycrystal/Amorphous':")
        l("    xax = parametersSample['Abscissa']")
        l("    xax = eval(xax)")
        l("    print(xax)")
        l("    print(type(xax))")
        l("else:")
        l("    xax = ['|Q|']")
        l("xax_str = ', '.join(xax)")
        l("print(xax_str)")
        # boolean for single crystal sample
        l("if parametersSample['Type'] == 'Single Crystal':")
        l("    singleCrystal = 'True'")
        l("else:")
        l("    singleCrystal = 'False'")
        l()
        # for loop through the runs of the sample data
        l("for files_run in range(len(files)):")
        l("    files_run_str = ', '.join(files[files_run])")
        l()
        # load sample data returns detector rotations in sample data and
        # omegas of the sample for single crystal samples
        l("    parameters = DNSLoadData(DataPath=data_path, OutputWorkspace=workspaces[files_run], \n"
          "                             OutputTable='SampleDataTable', XAxisUnit=xax_str, Wavelength=wavelength, \n"
          "                             DataX=dataX_str, MaskAngles=maskAnglesStr, FilesList=files_run_str, \n"
          "                             SampleParameters=str(parametersSample), SingleCrystal=singleCrystal, \n"
          "                             Normalization=norm)")
        l("    deterotas = parameters.split(';')[0]")
        l("    omegas    = parameters.split(';')[1]")
        l("    sample_table = mtd[workspaces[files_run]+'_SampleDataTable']")
        l("    if detEffi:")
        # load standard data for detector efficiency correction
        l("        DNSLoadData(DataPath=std_path, OutputWorkspace=workspaces[files_run], OutputTable='VanaDataTable',"
          "                    XAxisUnit=xax_str, Wavelength=wavelength, DataX=dataX_str, MaskAngles=maskAnglesStr,"
          "                    RefWorkspaces=sample_table, Deterotas=deterotas, Normalization=norm,"
          "                    StandardType='vana')")
        l("    if flipRatio:")
        # load standard data for flipping ratio correction
        l("        DNSLoadData(DataPath=std_path, OutputWorkspace=workspaces[files_run], OutputTable='NicrDataTable',"
          "                    XAxisUnit=xax_str, Wavelength=wavelength, DataX=dataX_str, MaskAngles=maskAnglesStr,"
          "                    RefWorkspaces=sample_table, Deterotas=deterotas, Normalization=norm,"
          "                    StandardType='nicr')")
        l("    if detEffi or flipRatio or subInst:")
        # load standard data for instrument background data
        l("        DNSLoadData(DataPath=std_path, OutputWorkspace=workspaces[files_run], "
          "                    OutputTable='BackgroundDataTable', XAxisUnit=xax_str, Wavelength=wavelength, "
          "                    DataX=dataX_str, MaskAngles=maskAnglesStr, RefWorkspaces=sample_table, "
          "                    Deterotas=deterotas, Normalization=norm, StandardType='leer')")
        # save sample data in table with their background workspace
        # returns list of polarisation in the data
        l("        polarisations = DNSProcessStandardData(SampleTable=workspaces[files_run]+'_SampleDataTable', "
          "                                               BackgroundTable=workspaces[files_run]+'_BackgroundDataTable',"
          "                                               OutputWorkspace=workspaces[files_run],"
          "                                               OutputTable='ProcessedDataTable')")
        l("        sample_table = mtd[workspaces[files_run]+'_ProcessedDataTable']")
        l("    if detEffi:")
        # save vanadium workspaces in table and assign coefficients to sample workspaces
        l("        DNSProcessVanadium(SampleTable=workspaces[files_run]+'_ProcessedDataTable', "
          "                           VanadiumTable=workspaces[files_run]+'_VanaDataTable',"
          "                           OutputWorkspace=workspaces[files_run], OutputXAxis=xax_str, "
          "                           Polarisations=polarisations, SingleCrystal=singleCrystal)")
        l("        sample_table = mtd[workspaces[files_run]+'_SampleTableVanaCoef']")
        l("    if flipRatio:")
        # save nickel chrome workspaces in table and assign coefficients to sample workspaces
        l("        DNSProcessNiCr(SampleTable=sample_table, NiCrTable=workspaces[files_run]+'_NicrDataTable', "
          "                       OutputWorkspace=workspaces[files_run], XAxisUnits=xax_str, "
          "                       Polarisations=polarisations, FlipCorrFactor=str(flipFac), "
          "                       SingleCrystal=singleCrystal)")
        l("        sample_table = mtd[workspaces[files_run]+'_SampleTableNiCrCoef']")
        l("    if saveToFile:")
        # do reduction/correction and save to file
        l("        DNSProcessSampleData(SampleTable=sample_table, SubtractBackground=str(subInst),"
          "                             SubtractBackgroundFactor=subInstFac, DeteEffiCorrection=str(detEffi),"
          "                             FlipRatioCorrection=str(flipRatio), SampleParameters=str(parametersSample),"
          "                             OutputWorkspace=workspaces[files_run],OutputXAxis=xax_str,"
          "                             Comment=comments[files_run], Omegas=omegas, OutputFileDirectory=fileDirectory,"
          "                             OutputFilePrefix=filePrefix)")
        l("    else:")
        # do reduction/correction
        l("        DNSProcessSampleData(SampleTable=sample_table, SubtractBackground=str(subInst),"
          "                             SubtractBackgroundFactor=subInstFac, DeteEffiCorrection=str(detEffi),"
          "                             FlipRatioCorrection=str(flipRatio), SampleParameters=str(parametersSample), "
          "                             OutputWorkspace=workspaces[files_run], OutputXAxis=xax_str,"
          "                             Comment=comments[files_run], Omegas=omegas)")

        return script[0]


class DNSReductionScripter(BaseReductionScripter):

    def __init__(self, name, facility):
        BaseReductionScripter.__init__(self, name, facility)
