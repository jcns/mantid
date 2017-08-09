from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import StringListValidator, Direction
from mantid.simpleapi import LoadDNSLegacy, GroupWorkspaces, CreateLogPropertyTable, CompareSampleLogs, \
    DeleteWorkspace, AddSampleLog, DNSMergeRuns, CloneWorkspace, Divide, LoadEmptyInstrument, MergeRuns, MaskAngle
from mantid.dataobjects import Workspace2D

import numpy as np

from scipy.constants import m_n, h, physical_constants

import os

from collections import OrderedDict


class DNSLoadData(PythonAlgorithm):
    """
    Load fi;es and save in workspaces
    """

    def _extract_norm_workspace(self, ws_group):
        """
        extract the norm from workspace group and save in other workspace group
        :param ws_group: workspace group
        """
        norm_dict = {"time": "duration", "monitor": "mon_sum"}
        norm_list = []

        for i in range(ws_group.getNumberOfEntries()):
            ws = ws_group.getItem(i)
            norm_ws = CloneWorkspace(ws, OutputWorkspace=ws.getName()+self._suff_norm)
            val = float(ws.getRun().getProperty(norm_dict[self._norm]).value)

            for i in range(len(norm_ws.extractY())):
                norm_ws.setY(i, np.array([val]))
                norm_ws.setE(i, np.array([0.0]))

            norm_list.append(norm_ws.getName())

        GroupWorkspaces(norm_list, OutputWorkspace=ws_group.getName()+self._suff_norm)

    def _merge_and_normalize(self, ws_group):
        """
        merge and normalize workspace group
        :param ws_group: workspace group
        """
        xaxis = self.xax.split(", ")
        for x in xaxis:
            data_merged = DNSMergeRuns(ws_group, x, OutputWorkspace=ws_group+"_m0_"+x)
            norm_merged = DNSMergeRuns(ws_group+self._suff_norm, x, OutputWorkspace=ws_group+self._suff_norm+"_m_"+x)
            try:
                Divide(data_merged, norm_merged, OutputWorkspace=ws_group+"_m_"+x)
            except:
                data_x = data_merged.extractX()
                norm_merged.setX(0, data_x[0])
                Divide(data_merged, norm_merged, OutputWorkspace=ws_group+"_m_"+x)

    def _load_ws_sample(self, data_path, files, wavelength, ei, dataX):
        """
        load sample data and save into workspaces
        :param data_path: path to sample data files
        :param files: list of names of the sample data files
        :param wavelength: wavelength for the loaded workspace
        :param ei: ei for loaded workspace
        :param dataX: x data if wavelength is different
        """
        self._data_files      = files.split(", ")
        self._data_workspaces = []

        for f in self._data_files:
            ws_name   = os.path.splitext(f)[0]
            file_path = os.path.join(data_path, f)
            LoadDNSLegacy(Filename=file_path, OutputWorkspace=ws_name, Normalization="no")

            if wavelength:
                AddSampleLog(ws_name, "wavelength", str(wavelength), "Number", "Angstrom")
                AddSampleLog(ws_name, "Ei",         str(ei),         "Number", "meV")
                for i in range(mtd[ws_name].getNumberHistograms()):
                    mtd[ws_name].setX(i, dataX)

            self._data_workspaces.append(ws_name)

        self._deterota = []
        self.omegas    = []

        # save all deterotas and omeagas to group workspaces
        for wsp_name in self._data_workspaces:
            angle = mtd[wsp_name].getRun().getProperty("deterota").value
            omega = mtd[wsp_name].getRun().getProperty("omega").value
            omega = round(omega, 1)

            if self.sc == "True" and not self._is_in_omega_list(self.omegas, omega):
                self.omegas.append(round(omega, 1))

            if not self._is_in_list(self._deterota, angle, self.tol):
                self._deterota.append(angle)

        self._group_ws(self._data_workspaces, self._deterota, self.omegas)

    def _load_ws_standard(self, data_path, ref_ws, wavelength, ei, dataX):
        """
        load standard data and save into workspaces
        :param data_path: path to standard data
        :param ref_ws: workspaces to compare the new workspaces to
        :param wavelength: wavelength for the loaded workspace
        :param ei: ei for loaded workspace
        :param dataX: x data if wavelength is different
        """
        # all workspaces of sample data, also false ones
        all_calibration_workspaces = []

        for f in os.listdir(data_path):
            full_file_name = os.path.join(data_path, f)

            if os.path.isfile(full_file_name) and self.std_type in full_file_name:
                ws_name = os.path.splitext(f)[0]

                if not mtd.doesExist(ws_name):
                    LoadDNSLegacy(Filename=full_file_name, OutputWorkspace=ws_name, Normalization="no")
                if ws_name not in all_calibration_workspaces:
                    all_calibration_workspaces.append(ws_name)

        coil_currents = "C_a,C_b,C_c,C_z"
        sample_ws     = [mtd[ref_ws].cell(i, 0) for i in range(mtd[ref_ws].rowCount())]

        # workspaces to work with
        calibration_workspaces = []

        keep = False

        # delete if it has false sample logs
        for wsp_name in all_calibration_workspaces:

            for workspace in sample_ws:
                result = CompareSampleLogs([workspace, wsp_name], coil_currents, 0.01)
                if not result:
                    keep = True

            if not keep:
                DeleteWorkspace(wsp_name)
            else:
                if wavelength:
                    AddSampleLog(wsp_name, "wavelength", str(wavelength), "Number", "Angstrom")
                    AddSampleLog(wsp_name, "Ei",         str(ei),         "Number", "meV")
                    for i in range(mtd[wsp_name].getNumberHistograms()):
                        mtd[wsp_name].setX(i, dataX)
                calibration_workspaces.append(wsp_name)

        # save deterotas to group workspaces
        self.deterota = []

        for wsp_name in sample_ws:
            angle = mtd[wsp_name].getRun().getProperty("deterota").value
            if not self._is_in_list(self.deterota, angle, self.tol):
                self.deterota.append(angle)

        self._group_ws(calibration_workspaces, self.deterota)

    def _group_ws(self, ws, deterota, omegas=""):
        """
        group the workspaces
        :param ws: workspaces to be grouped
        :param deterota: deterotas in the workspaces
        :param omegas: omegas of the workspaces
        """

        if self.sc == "True":
            # sort workspaces by deterota and omegas
            self._sort_ws_omega(ws, deterota, omegas)
        else:
            # sort workspaces by deterota
            self._sort_ws(ws, deterota)

        group_names = []

        # create group names
        if ws:
            if "vana" in ws[0]:
                for pol in ["x", "y", "z"]:
                    for flip in ["sf", "nsf"]:
                        group_names.append(self.out_ws_name+"_rawvana_"+pol+"_"+flip)
            elif "nicr" in ws[0]:
                for pol in ["x", "y", "z"]:
                    for flip in ["sf", "nsf"]:
                        group_names.append(self.out_ws_name+"_rawnicr_"+pol+"_"+flip)
            elif "leer" in ws[0]:
                for pol in ["x", "y", "z"]:
                    for flip in ["sf", "nsf"]:
                        group_names.append(self.out_ws_name+"_leer_"+pol+"_"+flip)
            else:
                for pol in ["x", "y", "z"]:
                    for flip in ["sf", "nsf"]:
                        if self.sc == "True":
                            for o in omegas:
                                group_names.append(self.out_ws_name+"_rawdata_"+pol+"_"+flip+"_omega_"+str(o))
                        else:
                            group_names.append(self.out_ws_name+"_rawdata_"+pol+"_"+flip)

            # create workspace groups and norm them
            self._group_and_norm(group_names)

    def _sort_ws_omega(self, ws, deterota, omegas):
        """
        sort workspaces by deterotas and omegas
        :param ws: list of workspaces
        :param deterota: list of deterotas
        :param omegas: list of omegas
        """

        # dictionaries of polarisations and spin filp / non spin filp
        self.x_sf  = {}
        self.x_nsf = {}
        self.y_sf  = {}
        self.y_nsf = {}
        self.z_sf  = {}
        self.z_nsf = {}

        # create dictionary of deterotas in every dictionary of polarisations and fipps for every omega
        print(omegas)
        for omega in omegas:
            self.x_sf[omega]  = dict.fromkeys(deterota)
            self.x_nsf[omega] = dict.fromkeys(deterota)
            self.y_sf[omega]  = dict.fromkeys(deterota)
            self.y_nsf[omega] = dict.fromkeys(deterota)
            self.z_sf[omega]  = dict.fromkeys(deterota)
            self.z_nsf[omega] = dict.fromkeys(deterota)

        # sort workspaces in dictionaries
        for wsname in ws:
            print(wsname)
            run   = mtd[wsname].getRun()
            angle = run.getProperty("deterota").value
            flip  = run.getProperty("flipper").value
            pol   = run.getProperty("polarisation").value
            omega = round(run.getProperty("omega").value,1)

            for key in deterota:
                if np.fabs(angle - key) < self.tol:
                    angle = key

            if flip == "ON":
                if pol == "x":
                    if angle in self.x_sf[omega].keys() and bool(self.x_sf[omega][angle]):
                        self._sum_same(ws, self.x_sf[omega], angle, wsname)
                    else:
                        self.x_sf[omega][angle] = wsname
                elif pol == "y":
                    if angle in self.y_sf[omega].keys() and bool(self.y_sf[omega][angle]):
                        self._sum_same(ws, self.y_sf[omega], angle, wsname)
                    else:
                        self.y_sf[omega][angle] = wsname
                else:
                    if angle in self.z_sf[omega].keys() and bool(self.z_sf[omega][angle]):
                        self._sum_same(ws, self.z_sf[omega], angle, wsname)
                    else:
                        self.z_sf[omega][angle] = wsname
            else:
                if pol == "x":
                    if angle in self.x_nsf[omega].keys() and bool(self.x_nsf[omega][angle]):
                        self._sum_same(ws, self.x_nsf[omega], angle, wsname)
                    else:
                        self.x_nsf[omega][angle] = wsname
                elif pol == "y":
                    if angle in self.y_nsf[omega].keys() and bool(self.y_nsf[omega][angle]):
                        self._sum_same(ws, self.y_nsf[omega], angle, wsname)
                    else:
                        self.y_nsf[omega][angle] = wsname
                else:
                    if angle in self.z_nsf[omega].keys() and bool(self.z_nsf[omega][angle]):
                        self._sum_same(ws, self.z_nsf[omega], angle, wsname)
                    else:
                        self.z_nsf[omega][angle] = wsname

    def _sort_ws(self, ws, deterota):
        """
        sort workspaces by deterota
        :param ws: list of workspaces
        :param deterota: list of deterota
        """
        # create dictionaries with deterotas for polarisations and flips
        self._dic_from_keys(deterota)

        # sort workspaces to dictionaries
        for wsname in ws:

            run   = mtd[wsname].getRun()
            angle = run.getProperty("deterota").value
            flip  = run.getProperty("flipper").value
            pol   = run.getProperty("polarisation").value

            angle = self._angle_from_deterota(deterota, angle)

            if flip == "ON":
                if pol == "x":
                    if angle in self.x_sf.keys() and bool(self.x_sf[angle]):
                        self._sum_same(ws, self.x_sf, angle, wsname)
                    elif angle in self.x_sf.keys() or not self.deterotasIn:
                        self.x_sf[angle] = wsname
                elif pol == "y":
                    if angle in self.y_sf.keys() and bool(self.y_sf[angle]):
                        self._sum_same(ws, self.y_sf, angle, wsname)
                    elif angle in self.x_sf.keys() or not self.deterotasIn:
                        self.y_sf[angle] = wsname
                else:
                    if angle in self.z_sf.keys() and bool(self.z_sf[angle]):
                        self._sum_same(ws, self.z_sf, angle, wsname)
                    elif angle in self.x_sf.keys() or not self.deterotasIn:
                        self.z_sf[angle] = wsname
            else:
                if pol == "x":
                    if angle in self.x_nsf.keys() and bool(self.x_nsf[angle]):
                        self._sum_same(ws, self.x_nsf, angle, wsname)
                    elif angle in self.x_sf.keys() or not self.deterotasIn:
                        self.x_nsf[angle] = wsname
                elif pol == "y":
                    if angle in self.y_nsf.keys() and bool(self.y_nsf[angle]):
                        self._sum_same(ws, self.y_nsf, angle, wsname)
                    elif angle in self.x_sf.keys() or not self.deterotasIn:
                        self.y_nsf[angle] = wsname
                else:
                    if angle in self.z_nsf.keys() and bool(self.z_nsf[angle]):
                        self._sum_same(ws, self.z_nsf, angle, wsname)
                    elif angle in self.x_sf.keys() or not self.deterotasIn:
                        self.z_nsf[angle] = wsname

        # order dictionaries by deterotas
        self._order_dicts()

    def _group_and_norm(self, group_names):
        """
        group and norm workspaces
        :param group_names: names of the workspaces groups
        """
        for var in group_names:
            g_name = var+"_group"
            # get dictionaries with ordered workspaces by workspace names for single crystal
            if self.sc == "True":
                index = len(self.out_ws_name) + len("_rawdata_")

                ws_n = var[index:index+5]
                if ws_n[len(ws_n)-1:] == "_":
                    ws_n = ws_n[:-1]

                for i in reversed(range(len(var))):
                    if var[i] == "_":
                        index_o = i
                        break
                omega = var[index_o+1:]

                ws = eval("self."+ws_n)
                wsp = ws[float(omega)].values()

                # group workspaces and mask detectors
                if None not in wsp:
                    GroupWorkspaces(wsp, OutputWorkspace=g_name)
                    for angles in self.mask_angles:
                        (minAngle, maxAngle) = angles
                        MaskAngle(g_name, MinAngle=float(minAngle), MaxAngle=float(maxAngle))
                    self._use_ws.append(g_name)
            else:
                # get dictionaries with ordered workspaces by workspace names
                ws_n = var[-5:]
                if ws_n[0] == "_":
                    ws_n = ws_n[1:]
                wsp = eval("self."+ws_n).values()

                # group workspaces and mask detectors
                if None not in wsp:
                    GroupWorkspaces(wsp, OutputWorkspace=g_name)
                    for angles in self.mask_angles:
                        (minAngle, maxAngle) = angles
                        MaskAngle(g_name, MinAngle=float(minAngle), MaxAngle=float(maxAngle))
                    self._use_ws.append(g_name)
                # if seperation should be 'XYZ' there must be sample data for all polarisations
                elif "data" in var:
                    if self.sample_parameters["Type"] == "Polycrystal/Amorphous" and \
                                    self.sample_parameters["Separation"] == "XYZ":
                        raise RuntimeError("You can't separate with XYZ if there is only data with one separation")

        # merge and normalize groups
        for var in group_names:
            g_name = var+"_group"

            group_exist = True
            try:
                mtd[g_name]
            except:
                group_exist = False

            if group_exist:
                # add group name to sample logs to easily insert the groups in the tables
                AddSampleLog(mtd[g_name], LogName="ws_group", LogText=g_name)
                self._extract_norm_workspace(mtd[g_name])
                if self._m_and_n and not self.sc:
                    self._merge_and_normalize(g_name)
                elif self._m_and_n and self.sc:
                    x = self.xax.split(", ")[0]
                    DNSMergeRuns(g_name, x, OutputWorkspace=g_name+"_m_"+x)

    def _sum_same(self, ws_list, group_list, angle, ws_name):
        """
        sum workspaces if the polarisation, flipp, deterota and omega (if single crystal sample) is the same
        :param ws_list: list of the workspaces to be grouped
        :param group_list: list of grouped workspaces
        :param angle: angle of the deterota
        :param ws_name: workspace to be summed
        """
        old_ws = group_list[angle]
        new_name = old_ws

        if not mtd[old_ws].getRun().hasProperty("run_number"):
            AddSampleLog(old_ws, "run_number", old_ws)

        if not mtd[ws_name].getRun().hasProperty("run_number"):
            AddSampleLog(ws_name, "run_number", ws_name)

        new_ws = MergeRuns([old_ws, ws_name], OutputWorkspace=new_name)
        new_ws.setTitle(old_ws)
        loc = ws_list.index(ws_name)
        ws_list[loc] = old_ws
        DeleteWorkspace(ws_name)

    def _dic_from_keys(self, deterota):
        """
        create dictionaries with deterotas for polarisations and flipps
        :param deterota: list of deterotas
        """

        self.x_sf  = dict.fromkeys(deterota)
        self.x_nsf = dict.fromkeys(deterota)
        self.y_sf  = dict.fromkeys(deterota)
        self.y_nsf = dict.fromkeys(deterota)
        self.z_sf  = dict.fromkeys(deterota)
        self.z_nsf = dict.fromkeys(deterota)

    def _angle_from_deterota(self, deterota, angle):
        """
        replaces angle with other if there is an angle with less difference than the tolerance from this angle 
        in the list of deterotas 
        :param deterota: list of deterotas
        :param angle: angle to check if it will be replaced
        :return: angle
        """

        for key in deterota:
            if np.fabs(angle - key) < self.tol:
                angle = key
        return angle

    def _is_in_list(self, angle_list, angle, tolerance):
        """
        checks if the angle is in the list of angles 
        (or an angle with less difference than the tolerance from the angle)
        :param angle_list: list of angles
        :param angle: angle to be checked
        :param tolerance: tolerance for angle
        :return: true if angle is in list
        """
        for a in angle_list:
            if np.fabs(a - angle) < tolerance:
                return True
        return False

    def _is_in_omega_list(self, omega_list, omega):
        """
        checks if omega is in list
        :param omega_list: list of omegas
        :param omega: omega to be checked
        """
        for o in omega_list:
            if o == omega:
                return True
        return False

    def _order_dicts(self):
        """
        order dicts to ensure that the right workspaces will be set against
        """
        self.x_sf  = OrderedDict(sorted(self.x_sf.items()))
        self.x_nsf = OrderedDict(sorted(self.x_nsf.items()))
        self.y_sf  = OrderedDict(sorted(self.y_sf.items()))
        self.y_nsf = OrderedDict(sorted(self.y_nsf.items()))
        self.z_sf  = OrderedDict(sorted(self.z_sf.items()))
        self.z_nsf = OrderedDict(sorted(self.z_nsf.items()))

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name="DataPath",         defaultValue="",      doc="Path to the files to be load")
        self.declareProperty(name="OutputWorkspace",  defaultValue="",      doc="Name of the output workspace")
        self.declareProperty(name="OutputTable",      defaultValue="",      doc="Name of the output table")
        self.declareProperty(name="XAxisUnit",        defaultValue="",      doc="Units for the output x-axis")
        self.declareProperty(name="Wavelength",       defaultValue="",      doc="Wavelength for the workspaces")
        self.declareProperty(name="DataX",            defaultValue="",
                             doc="List of the x data for changing wavelength")
        self.declareProperty(name="MaskAngles",       defaultValue="",
                             doc="List of the angles of the detectors to be masked")
        self.declareProperty(name="FilesList",        defaultValue="",      doc="List of files of the data to be load")
        self.declareProperty(name="SampleParameters", defaultValue="{}",    doc="Dictionaries of sample data parameters")
        self.declareProperty(name="SingleCrystal",    defaultValue="False", doc="Boolean if sample is single crystal")
        self.declareProperty(name="RefWorkspaces",    defaultValue="",      doc="Referenced Workspace, to check data")
        self.declareProperty(name="Deterotas",        defaultValue="",      doc="List of deterotas")
        self.declareProperty(name="Normalization",    defaultValue="",
                             validator=StringListValidator(["time", "monitor"]),      doc="Type of normalization")
        self.declareProperty(name="StandardType",     defaultValue="vana",
                             validator=StringListValidator(["vana", "nicr", "leer"]), doc="Type of standard data")
        self.declareProperty(name="Parameters", defaultValue="", direction=Direction.Output,
                             doc="Deterotas and omegas of the data")

    def PyExec(self):

        data_path = self.getProperty("DataPath").value
        files     = self.getProperty("FilesList").value

        ref_ws = self.getProperty("RefWorkspaces").value

        self.out_ws_name = self.getProperty("OutputWorkspace").value
        self.xax         = self.getProperty("XAxisUnit").value
        table_name       = self.out_ws_name+"_"+self.getProperty("OutputTable").value

        wavelength = float(self.getProperty("Wavelength").value)
        if wavelength:
            ei = 0.5*h*h*1000.0/(m_n*wavelength*wavelength*1e-20)/physical_constants["electron volt"][0]
        else:
            ei = 0

        data_x1 = self.getProperty("DataX").value
        if data_x1:
            data_x = data_x1.split(", ")
            data_x = [float(x) for x in data_x]
            dataX = np.array(data_x)
        else:
            dataX = []

        mask_angles = self.getProperty("MaskAngles").value
        self.mask_angles = []
        if mask_angles:
            mask = mask_angles.split("; ")
            self.mask_angles = [eval(s) for s in mask]

        parameters = self.getProperty("SampleParameters").value
        self.sample_parameters = eval(parameters)
        self.sc = self.getProperty("SingleCrystal").value

        deterotasIn = self.getProperty("Deterotas").value
        if deterotasIn:
            self.deterotasIn = [float(det) for det in deterotasIn.split(", ")]
        else:
            self.deterotasIn = []

        self.std_type   = self.getProperty("StandardType").value

        self._norm = self.getProperty("Normalization").value

        tmp = LoadEmptyInstrument(InstrumentName="DNS")
        self._instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self._suff_norm = self._instrument.getStringParameter("normws_suffix")[0]
        self.tol        = float(self._instrument.getStringParameter("two_theta_tolerance")[0])
        self._m_and_n   = self._instrument.getBoolParameter("keep_intermediate_workspace")[0]

        self._use_ws = []

        if files:
            self._load_ws_sample(data_path, files, wavelength, ei, dataX)
            deterotas = [str(dete) for dete in self._deterota]
            deterotas = ", ".join(deterotas)

            if self.sc:
                omegas = [str(o) for o in self.omegas]
                omegas = ", ".join(omegas)
            else:
                omegas = ""
        else:
            self._load_ws_standard(data_path, ref_ws, wavelength, ei, dataX)
            deterotas = ""
            omegas    = ""

        self.setProperty("Parameters", deterotas+"; "+omegas)

        # create table from sample logs
        logs = ["run_title", "polarisation", "flipper", "deterota", "ws_group"]
        if self.sc:
            logs.append("omega")
        if self._use_ws:
            CreateLogPropertyTable(self._use_ws, OutputWorkspace=table_name, LogPropertyNames=logs, GroupPolicy="All")

        for i in mtd.getObjectNames():
            if isinstance(mtd[i], Workspace2D) and not mtd[i].getRun().hasProperty("ws_group") and "group" not in i:
                DeleteWorkspace(i)

AlgorithmFactory.subscribe(DNSLoadData)
