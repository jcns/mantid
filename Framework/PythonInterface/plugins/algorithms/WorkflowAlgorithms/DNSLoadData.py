from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import logger, StringListValidator
from mantid.simpleapi import LoadDNSLegacy, GroupWorkspaces, CreateLogPropertyTable, CompareSampleLogs, \
    DeleteWorkspace, AddSampleLog, DNSMergeRuns, CloneWorkspace, Divide, LoadEmptyInstrument, MergeRuns

import numpy as np

import os

from collections import OrderedDict


class DNSLoadData(PythonAlgorithm):

    def _extract_norm_workspace(self, wsgroup):
        norm_dict = {'time': 'duration', 'monitor': 'mon_sum'}
        normlist = []
        for i in range(wsgroup.getNumberOfEntries()):
            ws = wsgroup.getItem(i)
            normws = CloneWorkspace(ws, OutputWorkspace=ws.getName() + self._suff_norm)
            val = ws.getRun().getProperty(norm_dict[self._norm]).value
            for i in range(len(normws.extractY())):
                normws.setY(i, np.array([val]))
                normws.setE(i, np.array([0.0]))
            normlist.append(normws.getName())
        GroupWorkspaces(normlist, OutputWorkspace=wsgroup.getName() + self._suff_norm)

    def _merge_and_normalize(self, wsgroup, xax, namex= ''):
        xaxis = xax.split(', ')
        for x in xaxis:
            data_merged = DNSMergeRuns(wsgroup + namex, x, OutputWorkspace=wsgroup + '_m0' + '_' + x)
            norm_merged = DNSMergeRuns(wsgroup + self._suff_norm + namex, x,
                                       OutputWorkspace=wsgroup + self._suff_norm + '_m' + '_' + x)
            try:
                Divide(data_merged, norm_merged, OutputWorkspace=wsgroup + '_m' + '_' + x)
            except:
                dataX = data_merged.extractX()
                norm_merged.setX(0, dataX[0])
                Divide(data_merged, norm_merged, OutputWorkspace=wsgroup+'_m' + '_' + x)

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name='DataPath', defaultValue='', doc='Path to the files to be load')
        self.declareProperty(name='FilesList', defaultValue='',
                             doc='List of files of the data to be load')
        self.declareProperty(name='StandardType', defaultValue='vana',
                             validator=StringListValidator(['vana', 'nicr', 'leer']),
                             doc = 'Type of standard data')
        self.declareProperty(name='RefWorkspaces', defaultValue='', doc='Referenced Workspace, to check the data')
        self.declareProperty(name='OutputWorkspace', defaultValue='', doc='Name of the output workspace')
        self.declareProperty(name="OutputTable", defaultValue='',
                             doc='Name of the output table')
        self.declareProperty(name='XAxisUnit', defaultValue='', doc='Units for the output x-axis')
        self.declareProperty(name='Normalization', defaultValue='', validator=StringListValidator(['time', 'duration']),
                             doc='Type of normalization')

    def is_in_list(self, angle_list, angle, tolerance):
        for a in angle_list:
            if np.fabs(a - angle) < tolerance:
                return True
        return False

    def _load_ws_sample(self):

        logger.debug(str(self._files))
        self._data_files = self._files.split(', ')
        logger.debug(str(self._data_files))
        self._data_workspaces = []
        for f in self._data_files:
            wname = os.path.splitext(f)[0]
            logger.debug(wname)
            filepath = os.path.join(self._data_path, f)
            LoadDNSLegacy(Filename=filepath, OutputWorkspace=wname, Normalization='no')
            self._data_workspaces.append(wname)
        logger.debug(str(self._data_workspaces))
        self._deterota = []
        for wsname in self._data_workspaces:
            angle = mtd[wsname].getRun().getProperty('deterota').value
            if not self.is_in_list(self._deterota, angle, self.tol):
                self._deterota.append(angle)
        logger.debug(str(self._deterota))
        self._group_ws(self._data_workspaces, self._deterota)

    def _load_ws_standard(self):
        logger.debug(self.std_type)
        allcalibrationworkspaces = []
        for f in os.listdir(self._data_path):
            full_file_name = os.path.join(self._data_path, f)
            if os.path.isfile(full_file_name) and self.std_type in full_file_name:
                wname = os.path.splitext(f)[0]
                logger.debug(wname)
                if not mtd.doesExist(wname):
                    LoadDNSLegacy(Filename=full_file_name, OutputWorkspace=wname, Normalization='no')
                if wname not in allcalibrationworkspaces:
                    allcalibrationworkspaces.append(wname)
        logger.debug(str(allcalibrationworkspaces))
        logger.debug(mtd[self._ref_ws].getName())
        coil_currents = 'C_a,C_b,C_c,C_z'
        sample_ws = [mtd[self._ref_ws].cell(i, 0) for i in range(mtd[self._ref_ws].rowCount())]
        calibrationworkspaces = []
        keep = False
        for wsname in allcalibrationworkspaces:
            for worksp in sample_ws:
                result = CompareSampleLogs([worksp, wsname], coil_currents, 0.01)
                if not result:
                    keep = True
            if not keep:
                DeleteWorkspace(wsname)
            else:
                calibrationworkspaces.append(wsname)

        logger.debug("all: "+str(allcalibrationworkspaces))
        logger.debug("cali: "+str(calibrationworkspaces))

        for wsname in sample_ws:
            self.deterota = []
            angle = mtd[wsname].getRun().getProperty('deterota').value
            if not self.is_in_list(self.deterota, angle, self.tol):
                self.deterota.append(angle)

        self._group_ws(calibrationworkspaces, self.deterota)

    def _sum_same(self, ws_list, group_list, angle, ws_name):
        old_ws = group_list[angle]
        if mtd[old_ws].getRun().hasProperty('run_number'):
            print(mtd[old_ws].getRun().getProperty('run_number').value)
        new_name = old_ws
        if not mtd[old_ws].getRun().hasProperty('run_number'):
            AddSampleLog(old_ws, 'run_number', old_ws)
        if not mtd[ws_name].getRun().hasProperty('run_number'):
            AddSampleLog(ws_name, 'run_number', ws_name)
        new_ws = MergeRuns([old_ws, ws_name], OutputWorkspace=new_name)
        new_ws.setTitle(old_ws)
        loc = ws_list.index(ws_name)
        ws_list[loc] = old_ws
        print('ws_list after sum same: ', str(ws_list))
        DeleteWorkspace(ws_name)

    def sort_ws(self, ws, deterota):

        self.x_sf =dict.fromkeys(deterota)
        self.x_nsf = dict.fromkeys(deterota)
        self.y_sf = dict.fromkeys(deterota)
        self.y_nsf = dict.fromkeys(deterota)
        self.z_sf = dict.fromkeys(deterota)
        self.z_nsf = dict.fromkeys(deterota)
        for wsname in ws:
            run = mtd[wsname].getRun()
            angle = run.getProperty('deterota').value
            flipper = run.getProperty('flipper').value
            polarisation = run.getProperty('polarisation').value
            logger.debug(str(angle))
            logger.debug(str(flipper))
            logger.debug(str(polarisation))
            for key in deterota:
                if np.fabs(angle - key) < self.tol:
                    angle = key
            if flipper == 'ON':
                if polarisation == 'x':
                    if angle in self.x_sf.keys() and bool(self.x_sf[angle]):
                        self._sum_same(ws, self.x_sf, angle, wsname)
                    else:
                        self.x_sf[angle] = wsname
                elif polarisation == 'y':
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
                if polarisation == 'x':
                    if angle in self.x_nsf.keys() and bool(self.x_nsf[angle]):
                        self._sum_same(ws, self.x_nsf, angle, wsname)
                    else:
                        self.x_nsf[angle] = wsname
                elif polarisation == 'y':
                    if angle in self.y_nsf.keys() and bool(self.y_nsf[angle]):
                        self._sum_same(ws, self.y_nsf, angle, wsname)
                    else:
                        self.y_nsf[angle] = wsname
                else:
                    if angle in self.z_nsf.keys() and bool(self.z_nsf[angle]):
                        self._sum_same(ws, self.z_nsf, angle, wsname)
                    else:
                        self.z_nsf[angle] = wsname

        self.x_sf = OrderedDict(sorted(self.x_sf.items()))
        self.x_nsf = OrderedDict(sorted(self.x_nsf.items()))
        self.y_sf = OrderedDict(sorted(self.y_sf.items()))
        self.y_nsf = OrderedDict(sorted(self.y_nsf.items()))
        self.z_sf = OrderedDict(sorted(self.z_sf.items()))
        self.z_nsf = OrderedDict(sorted(self.z_nsf.items()))

    def _group_ws(self, ws, deterota):

        self.sort_ws(ws, deterota)

        group_names = []
        if ws:
            if 'vana' in ws[0]:
                for pol in ['x', 'y', 'z']:
                    for flip in ['sf', 'nsf']:
                        group_names.append(self._out_ws_name + '_rawvana_' + pol + '_' + flip)
            elif 'nicr' in ws[0]:
                for pol in ['x', 'y', 'z']:
                    for flip in ['sf', 'nsf']:
                        group_names.append(self._out_ws_name + '_rawnicr_' + pol + '_' + flip)
            elif 'leer' in ws[0]:
                for pol in ['x', 'y', 'z']:
                    for flip in ['sf', 'nsf']:
                        group_names.append(self._out_ws_name + '_leer_' + pol + '_' + flip)
            else:
                for pol in ['x', 'y', 'z']:
                    for flip in ['sf', 'nsf']:
                        group_names.append(self._out_ws_name + '_rawdata_' + pol + '_' + flip)

            self.group_and_norm(group_names)

    def group_and_norm(self, group_names):

        for var in group_names:
            gname = var + '_group'
            ws_n = var[-5:]
            if ws_n[0] == '_':
                ws_n = ws_n[1:]
            logger.debug(ws_n)
            wsp = eval('self.'+ws_n).values()
            if None not in wsp:
                GroupWorkspaces(wsp, OutputWorkspace=gname)
                self._use_ws.append(gname)
        for var in group_names:
            gname = var + '_group'
            group_exist = True
            try:
                mtd[gname]
            except:
                group_exist = False
            if group_exist:
                AddSampleLog(mtd[gname], LogName='ws_group', LogText=gname)
                self._extract_norm_workspace(mtd[gname])
                if self._m_and_n:
                    self._merge_and_normalize(gname, self.xax)

    def PyExec(self):

        self._data_path = self.getProperty('DataPath').value
        self._files = self.getProperty('FilesList').value
        self.std_type = self.getProperty('StandardType').value

        self._ref_ws = self.getProperty('RefWorkspaces').value
        self.xax = self.getProperty('XAxisUnit').value
        self._out_ws_name = self.getProperty('OutputWorkspace').value
        table_name = self._out_ws_name + '_' + self.getProperty('OutputTable').value
        self._norm = self.getProperty('Normalization').value

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self._instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self._suff_norm = self._instrument.getStringParameter("normws_suffix")[0]
        self.tol = float(self._instrument.getStringParameter("two_theta_tolerance")[0])
        self._m_and_n = self._instrument.getBoolParameter("keep_intermediate_workspace")[0]

        self._use_ws = []

        if self._files:
            self._load_ws_sample()
        else:
            self._load_ws_standard()
        logs = ['run_title', 'polarisation', 'flipper', 'deterota', 'ws_group']
        if self._use_ws:
            CreateLogPropertyTable(self._use_ws, OutputWorkspace=table_name, LogPropertyNames=logs, GroupPolicy='All')


AlgorithmFactory.subscribe(DNSLoadData)
