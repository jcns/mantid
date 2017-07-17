from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import StringListValidator
from mantid.simpleapi import LoadDNSLegacy, GroupWorkspaces, CreateLogPropertyTable, CompareSampleLogs, \
    DeleteWorkspace, AddSampleLog, DNSMergeRuns, CloneWorkspace, Divide, LoadEmptyInstrument, MergeRuns, MaskAngle

import numpy as np

from scipy.constants import m_n, h, physical_constants

import os

from collections import OrderedDict


class DNSLoadData(PythonAlgorithm):

    def _extract_norm_workspace(self, wsgroup):
        norm_dict = {'time': 'duration', 'monitor': 'mon_sum'}
        norm_list = []

        for i in range(wsgroup.getNumberOfEntries()):
            ws = wsgroup.getItem(i)
            norm_ws = CloneWorkspace(ws, OutputWorkspace=ws.getName()+self._suff_norm)
            val = float(ws.getRun().getProperty(norm_dict[self._norm]).value)

            for i in range(len(norm_ws.extractY())):
                norm_ws.setY(i, np.array([val]))
                norm_ws.setE(i, np.array([0.0]))

            norm_list.append(norm_ws.getName())

        GroupWorkspaces(norm_list, OutputWorkspace=wsgroup.getName()+self._suff_norm)

    def _merge_and_normalize(self, wsgroup):
        xaxis = self.xax.split(', ')
        for x in xaxis:
            data_merged = DNSMergeRuns(wsgroup,                 x, OutputWorkspace=wsgroup+'_m0'+'_'+x)
            norm_merged = DNSMergeRuns(wsgroup+self._suff_norm, x, OutputWorkspace=wsgroup+self._suff_norm+'_m'+'_'+x)
            try:
                Divide(data_merged, norm_merged, OutputWorkspace=wsgroup+'_m'+'_'+x)
            except:
                data_x = data_merged.extractX()
                norm_merged.setX(0, data_x[0])
                Divide(data_merged, norm_merged, OutputWorkspace=wsgroup+'_m'+'_'+x)

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name='DataPath',         defaultValue='',   doc='Path to the files to be load')
        self.declareProperty(name='FilesList',        defaultValue='',   doc='List of files of the data to be load')
        self.declareProperty(name='StandardType',     defaultValue='vana',
                             validator=StringListValidator(['vana', 'nicr', 'leer']), doc='Type of standard data')
        self.declareProperty(name='RefWorkspaces',    defaultValue='',   doc='Referenced Workspace, to check the data')
        self.declareProperty(name='OutputWorkspace',  defaultValue='',   doc='Name of the output workspace')
        self.declareProperty(name="OutputTable",      defaultValue='',   doc='Name of the output table')
        self.declareProperty(name='XAxisUnit',        defaultValue='',   doc='Units for the output x-axis')
        self.declareProperty(name='Normalization',    defaultValue='',
                             validator=StringListValidator(['time', 'monitor']), doc='Type of normalization')
        self.declareProperty(name='Wavelength',       defaultValue='',   doc='')
        self.declareProperty(name='DataX',            defaultValue='',   doc='')
        self.declareProperty(name='MaskAngles',       defaultValue='',   doc='')
        self.declareProperty(name='SampleParameters', defaultValue='{}', doc='')
        self.declareProperty(name='SingleCrystal',    defaultValue='False', doc='')

    def is_in_list(self, angle_list, angle, tolerance):

        for a in angle_list:
            if np.fabs(a - angle) < tolerance:
                return True

        return False

    def is_in_omega_list(self, omega_list, omega):

        for o in omega_list:
            if o == omega:
                return True

        return False

    def _load_ws_sample(self):

        self._data_files = self._files.split(', ')
        print(str(self._data_files))
        self._data_workspaces = []

        for f in self._data_files:
            ws_name   = os.path.splitext(f)[0]
            file_path = os.path.join(self._data_path, f)
            LoadDNSLegacy(Filename=file_path, OutputWorkspace=ws_name, Normalization='no')

            if self.wavelength:
                AddSampleLog(ws_name, 'wavelength', str(self.wavelength), 'Number', 'Angstrom')
                AddSampleLog(ws_name, 'Ei',         str(self.ei),         'Number', 'meV')

                for i in range(mtd[ws_name].getNumberHistograms()):
                    mtd[ws_name].setX(i, self.dataX)

            self._data_workspaces.append(ws_name)

        print(str(self._data_workspaces))
        self._deterota = []
        omegas = []

        for wsp_name in self._data_workspaces:
            angle = mtd[wsp_name].getRun().getProperty('deterota').value
            omega = mtd[wsp_name].getRun().getProperty('omega').value

            if self.sc == 'True' and not self.is_in_omega_list(omegas, omega):
                omegas.append(round(omega,1))

            if not self.is_in_list(self._deterota, angle, self.tol):
                self._deterota.append(angle)

        print(omegas)
        self._group_ws(self._data_workspaces, self._deterota, omegas)


    def _load_ws_standard(self):

        all_calibration_workspaces = []

        for f in os.listdir(self._data_path):
            full_file_name = os.path.join(self._data_path, f)

            if os.path.isfile(full_file_name) and self.std_type in full_file_name:
                ws_name = os.path.splitext(f)[0]

                if not mtd.doesExist(ws_name):
                    LoadDNSLegacy(Filename=full_file_name, OutputWorkspace=ws_name, Normalization='no')
                if ws_name not in all_calibration_workspaces:
                    all_calibration_workspaces.append(ws_name)

        coil_currents = 'C_a,C_b,C_c,C_z'
        sample_ws = [mtd[self._ref_ws].cell(i, 0) for i in range(mtd[self._ref_ws].rowCount())]
        calibration_workspaces = []
        keep = False

        for wsp_name in all_calibration_workspaces:

            for workspace in sample_ws:
                result = CompareSampleLogs([workspace, wsp_name], coil_currents, 0.01)
                if not result:
                    keep = True

            if not keep:
                DeleteWorkspace(wsp_name)
            else:
                if self.wavelength:
                    AddSampleLog(wsp_name, 'wavelength', str(self.wavelength), 'Number', 'Angstrom')
                    AddSampleLog(wsp_name, 'Ei',         str(self.ei),         'Number', 'meV')

                    for i in range(mtd[wsp_name].getNumberHistograms()):
                        mtd[wsp_name].setX(i, self.dataX)

                calibration_workspaces.append(wsp_name)

        for wsp_name in sample_ws:

            self.deterota = []
            angle = mtd[wsp_name].getRun().getProperty('deterota').value

            if not self.is_in_list(self.deterota, angle, self.tol):
                self.deterota.append(angle)

        self._group_ws(calibration_workspaces, self.deterota)

    def _sum_same(self, ws_list, group_list, angle, ws_name):

        print (ws_list)

        old_ws = group_list[angle]
        new_name = old_ws

        if not mtd[old_ws].getRun().hasProperty('run_number'):
            AddSampleLog(old_ws, 'run_number', old_ws)

        if not mtd[ws_name].getRun().hasProperty('run_number'):
            AddSampleLog(ws_name, 'run_number', ws_name)

        new_ws = MergeRuns([old_ws, ws_name], OutputWorkspace=new_name)
        new_ws.setTitle(old_ws)
        loc = ws_list.index(ws_name)
        ws_list[loc] = old_ws
        DeleteWorkspace(ws_name)
        print(ws_list)

    def sort_ws_omega(self, ws, deterota, omegas):
        print(omegas)

        self.x_sf = {}
        self.x_nsf = {}
        self.y_sf = {}
        self.y_nsf = {}
        self.z_sf = {}
        self.z_nsf = {}

        for omega in omegas:
            self.x_sf[omega] = dict.fromkeys(deterota)
            self.x_nsf[omega] = dict.fromkeys(deterota)
            self.y_sf[omega] = dict.fromkeys(deterota)
            self.y_nsf[omega] = dict.fromkeys(deterota)
            self.z_sf[omega] = dict.fromkeys(deterota)
            self.z_nsf[omega] = dict.fromkeys(deterota)

        for wsname in ws:
            print(ws)
            print(wsname)
            run   = mtd[wsname].getRun()
            angle = run.getProperty('deterota').value
            flip  = run.getProperty('flipper').value
            pol   = run.getProperty('polarisation').value
            omega = round(run.getProperty('omega').value,1)

            for key in deterota:
                if np.fabs(angle - key) < self.tol:
                    angle = key

            if flip == 'ON':
                if pol == 'x':
                    if angle in self.x_sf[omega].keys() and bool(self.x_sf[omega][angle]):
                        print('sum same: ', 'sfx , new: ', wsname, ' old: ', self.x_sf[omega])
                        self._sum_same(ws, self.x_sf[omega], angle, wsname)
                    else:
                        self.x_sf[omega][angle] = wsname
                elif pol == 'y':
                    if angle in self.y_sf[omega].keys() and bool(self.y_sf[omega][angle]):
                        print('sum same: ', 'sfy , new: ', wsname, ' old: ', self.y_sf[omega])
                        self._sum_same(ws, self.y_sf[omega], angle, wsname)
                    else:
                        self.y_sf[omega][angle] = wsname
                else:
                    if angle in self.z_sf[omega].keys() and bool(self.z_sf[omega][angle]):
                        print('sum same: ', 'sfz , new: ', wsname, ' old: ', self.z_sf[omega])
                        self._sum_same(ws, self.z_sf[omega], angle, wsname)
                    else:
                        self.z_sf[omega][angle] = wsname
            else:
                if pol == 'x':
                    if angle in self.x_nsf[omega].keys() and bool(self.x_nsf[omega][angle]):
                        print('sum same: ', 'nsfx , new: ', wsname, ' old: ', self.x_nsf[omega])
                        self._sum_same(ws, self.x_nsf[omega], angle, wsname)
                    else:
                        self.x_nsf[omega][angle] = wsname
                elif pol == 'y':
                    if angle in self.y_nsf[omega].keys() and bool(self.y_nsf[omega][angle]):
                        print('sum same: ', 'nsfy , new: ', wsname, ' old: ', self.y_nsf[omega])
                        self._sum_same(ws, self.y_nsf[omega], angle, wsname)
                    else:
                        self.y_nsf[omega][angle] = wsname
                else:
                    if angle in self.z_nsf[omega].keys() and bool(self.z_nsf[omega][angle]):
                        print('sum same: ', 'nsfz , new: ', wsname, ' old: ', self.z_nsf[omega])
                        self._sum_same(ws, self.z_nsf[omega], angle, wsname)
                    else:
                        self.z_nsf[omega][angle] = wsname

        print(omegas)

    def sort_ws(self, ws, deterota):

        self.x_sf  = dict.fromkeys(deterota)
        self.x_nsf = dict.fromkeys(deterota)
        self.y_sf  = dict.fromkeys(deterota)
        self.y_nsf = dict.fromkeys(deterota)
        self.z_sf  = dict.fromkeys(deterota)
        self.z_nsf = dict.fromkeys(deterota)

        for wsname in ws:

            run   = mtd[wsname].getRun()
            angle = run.getProperty('deterota').value
            flip  = run.getProperty('flipper').value
            pol   = run.getProperty('polarisation').value

            for key in deterota:
                if np.fabs(angle - key) < self.tol:
                    angle = key

            if flip == 'ON':
                if pol == 'x':
                    if angle in self.x_sf.keys() and bool(self.x_sf[angle]):
                        self._sum_same(ws, self.x_sf, angle, wsname)
                    else:
                        self.x_sf[angle] = wsname
                elif pol == 'y':
                    if angle in self.y_sf.keys() and bool(self.y_sf[angle]):
                        self._sum_same(ws, self.y_sf, angle, wsname)
                    else:
                        self.y_sf[angle] = wsname
                else:
                    if angle in self.z_sf.keys() and bool(self.z_sf[angle]):
                        self._sum_same(ws, self.z_sf, angle, wsname)
                    else:
                        self.z_sf[angle] = wsname
            else:
                if pol == 'x':
                    if angle in self.x_nsf.keys() and bool(self.x_nsf[angle]):
                        self._sum_same(ws, self.x_nsf, angle, wsname)
                    else:
                        self.x_nsf[angle] = wsname
                elif pol == 'y':
                    if angle in self.y_nsf.keys() and bool(self.y_nsf[angle]):
                        self._sum_same(ws, self.y_nsf, angle, wsname)
                    else:
                        self.y_nsf[angle] = wsname
                else:
                    if angle in self.z_nsf.keys() and bool(self.z_nsf[angle]):
                        self._sum_same(ws, self.z_nsf, angle, wsname)
                    else:
                        self.z_nsf[angle] = wsname

        self.x_sf  = OrderedDict(sorted(self.x_sf.items()))
        self.x_nsf = OrderedDict(sorted(self.x_nsf.items()))
        self.y_sf  = OrderedDict(sorted(self.y_sf.items()))
        self.y_nsf = OrderedDict(sorted(self.y_nsf.items()))
        self.z_sf  = OrderedDict(sorted(self.z_sf.items()))
        self.z_nsf = OrderedDict(sorted(self.z_nsf.items()))

    def _group_ws(self, ws, deterota, omegas=''):
        print(omegas)
        print(self.sc == 'True')

        if self.sc == 'True':
            self.sort_ws_omega(ws, deterota, omegas)
        else:
            self.sort_ws(ws, deterota)

        group_names = []
        if ws:
            if 'vana' in ws[0]:
                for pol in ['x', 'y', 'z']:
                    for flip in ['sf', 'nsf']:
                        group_names.append(self._out_ws_name+'_rawvana_'+pol+'_'+flip)
            elif 'nicr' in ws[0]:
                for pol in ['x', 'y', 'z']:
                    for flip in ['sf', 'nsf']:
                        group_names.append(self._out_ws_name+'_rawnicr_'+pol+'_'+flip)
            elif 'leer' in ws[0]:
                for pol in ['x', 'y', 'z']:
                    for flip in ['sf', 'nsf']:
                        group_names.append(self._out_ws_name+'_leer_'+pol+'_'+flip)
            else:
                for pol in ['x', 'y', 'z']:
                    for flip in ['sf', 'nsf']:
                        if self.sc == 'True':
                            for o in omegas:
                                group_names.append(self._out_ws_name+'_rawdata_'+pol+'_'+flip+'_omega_'+str(o))
                        else:
                            group_names.append(self._out_ws_name+'_rawdata_'+pol+'_'+flip)

            self.group_and_norm(group_names)

    def group_and_norm(self, group_names):

        for var in group_names:
            print(var)

            g_name = var+'_group'

            if self.sc == 'True':

                index = len(self._out_ws_name) + len ('_rawdata_')

                ws_n = var[index:index+5]

                if ws_n[len(ws_n)-1:] == '_':
                    ws_n = ws_n[:-1]

                for i in reversed(range(len(var))):
                    if var[i] == '_':
                        index_o = i
                        break

                omega = var[index_o+1:]

                print(ws_n)

                ws = eval('self.'+ws_n)
                print(ws)
                print(omega)

                wsp = ws[float(omega)].values()

                if None not in wsp:
                    GroupWorkspaces(wsp, OutputWorkspace=g_name)

                    for angles in self.mask_angles:
                        (minAngle, maxAngle) = angles
                        MaskAngle(g_name, MinAngle=float(minAngle), MaxAngle=float(maxAngle))

                    self._use_ws.append(g_name)

            else:

                ws_n   = var[-5:]

                if ws_n[0] == '_':
                    ws_n = ws_n[1:]

                wsp = eval('self.'+ws_n).values()

                if None not in wsp:
                    GroupWorkspaces(wsp, OutputWorkspace=g_name)

                    for angles in self.mask_angles:
                        (minAngle, maxAngle) = angles
                        MaskAngle(g_name, MinAngle=float(minAngle), MaxAngle=float(maxAngle))

                    self._use_ws.append(g_name)

                elif 'data' in var:
                    if self.sample_parameters["Type"] == 'Polycrystal/Amorphous' and \
                                    self.sample_parameters['Separation'] == 'XYZ':
                        raise RuntimeError("You can't separate with XYZ if there is only data with one separation")

        for var in group_names:
            g_name      = var+'_group'
            group_exist = True

            try:
                mtd[g_name]
            except:
                group_exist = False

            if group_exist:
                AddSampleLog(mtd[g_name], LogName='ws_group', LogText=g_name)
                self._extract_norm_workspace(mtd[g_name])
                if self._m_and_n:
                    self._merge_and_normalize(g_name)

    def PyExec(self):

        self._data_path = self.getProperty('DataPath').value
        self._files     = self.getProperty('FilesList').value
        self.std_type   = self.getProperty('StandardType').value

        self._ref_ws = self.getProperty('RefWorkspaces').value

        self.xax          = self.getProperty('XAxisUnit').value
        self._out_ws_name = self.getProperty('OutputWorkspace').value
        table_name        = self._out_ws_name + '_' + self.getProperty('OutputTable').value

        self._norm = self.getProperty('Normalization').value

        self.wavelength = float(self.getProperty('Wavelength').value)
        if self.wavelength:
            self.ei = 0.5*h*h*1000.0/(m_n*self.wavelength*self.wavelength*1e-20)/physical_constants['electron volt'][0]

        data_x1 = self.getProperty('DataX').value
        if data_x1:
            data_x = data_x1.split(', ')
            data_x = [float(x) for x in data_x]
            self.dataX = np.array(data_x)

        mask_angles = self.getProperty('MaskAngles').value
        self.mask_angles = []
        if mask_angles:
            mask = mask_angles.split('; ')
            self.mask_angles = [eval(s) for s in mask]

        parameters = self.getProperty('SampleParameters').value
        self.sample_parameters = eval(parameters)

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self._instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self._suff_norm = self._instrument.getStringParameter("normws_suffix")[0]
        self.tol        = float(self._instrument.getStringParameter("two_theta_tolerance")[0])
        self._m_and_n   = self._instrument.getBoolParameter("keep_intermediate_workspace")[0]

        self.sc = self.getProperty('SingleCrystal').value

        self._use_ws = []

        if self._files:
            self._load_ws_sample()
        else:
            self._load_ws_standard()

        logs = ['run_title', 'polarisation', 'flipper', 'deterota', 'ws_group']
        if self._use_ws:
            CreateLogPropertyTable(self._use_ws, OutputWorkspace=table_name, LogPropertyNames=logs, GroupPolicy='All')


AlgorithmFactory.subscribe(DNSLoadData)
