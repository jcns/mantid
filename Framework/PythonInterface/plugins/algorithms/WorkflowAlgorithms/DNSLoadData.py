from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd, PropertyMode
from mantid.kernel import logger, Direction, StringListValidator
from mantid.simpleapi import LoadDNSLegacy, GroupWorkspaces, CreateLogPropertyTable, CompareSampleLogs, \
    DeleteWorkspace, Plus, AddSampleLog, DNSMergeRuns, CloneWorkspace, Divide, LoadEmptyInstrument, MergeRuns
import mantid.simpleapi as sapi

import numpy as np

import os

from collections import OrderedDict

class DNSLoadData(PythonAlgorithm):

    def _extract_norm_workspace(self, wsgroup, norm):

        norm_dict = {'time': 'duration', 'monitor': 'mon_sum'}
        normlist = []
        for i in range(wsgroup.getNumberOfEntries()):
            ws = wsgroup.getItem(i)
            normws = CloneWorkspace(ws, OutputWorkspace=ws.getName() + self._suff_norm)
            logger.debug("run: " + str(ws.getRun()))
            logger.debug("name property: " + norm_dict[norm])
            logger.debug("property: " + str(ws.getRun().getProperty(norm_dict[norm])))
            logger.debug("property value: " + str(ws.getRun().getProperty(norm_dict[norm]).value))
            logger.debug("property value: " + str(ws.getRun().getProperty(norm_dict[norm]).value))
            val = ws.getRun().getProperty(norm_dict[norm]).value
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

        self.declareProperty(name='FilesList', defaultValue='',
                             doc='List of files of the Data you want to load')
        self.declareProperty(name='StandardType', defaultValue='vana',
                             validator=StringListValidator(['vana', 'nicr', 'leer']), doc = 'Which type of standarddata')
        self.declareProperty(name='RefWorkspaces', defaultValue='', doc='Referenced Workspace')
        self.declareProperty(name='DataPath', defaultValue='', doc='Path to the files')
        self.declareProperty(name='OutWorkspaceName', defaultValue='', doc='Name of the output workspace')
        self.declareProperty(name="OutputTable", defaultValue='',
                             doc='Name of the output table')
        self.declareProperty(name='XAxisUnit', defaultValue='')
        self.declareProperty(name='Normalization', defaultValue='')

    def is_in_list(self, angle_list, angle, tolerance):
        for a in angle_list:
            if np.fabs(a - angle) < tolerance:
                 return True
        return False

    def _load_ws_sample(self):

        _files = self.getProperty('FilesList').value
        logger.debug(str(_files))
        self._data_files = _files.split(', ')
        logger.debug(str(self._data_files))
        self._data_path = self.getProperty('DataPath').value
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
        std_type = self.getProperty('StandardType').value
        logger.debug(std_type)
        allcalibrationworkspaces = []
        self._data_path = self.getProperty('DataPath').value
        for f in os.listdir(self._data_path):
            full_file_name = os.path.join(self._data_path, f)
            if os.path.isfile(full_file_name) and std_type in full_file_name:
                wname = os.path.splitext(f)[0]
                logger.debug(wname)
                if not mtd.doesExist(wname):
                    LoadDNSLegacy(Filename=full_file_name, OutputWorkspace=wname, Normalization='no')
                if wname not in allcalibrationworkspaces:
                    allcalibrationworkspaces.append(wname)
        logger.debug(str(allcalibrationworkspaces))
        self._ref_ws = mtd[self.getProperty('RefWorkspaces').value]
        logger.debug(self._ref_ws.getName())
        coil_currents = 'C_a,C_b,C_c,C_z'
        sample_ws = [self._ref_ws.cell(i, 0) for i in range(len(self._ref_ws.column(0)))]
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

    def _group_ws(self, ws, deterota):
        x_sf = dict.fromkeys(deterota)
        x_nsf = dict.fromkeys(deterota)
        y_sf = dict.fromkeys(deterota)
        y_nsf = dict.fromkeys(deterota)
        z_sf = dict.fromkeys(deterota)
        z_nsf = dict.fromkeys(deterota)
        for wsname in ws:
            run = mtd[wsname].getRun()
            angle = run.getProperty('deterota').value
            flipper = run.getProperty('flipper').value
            polarisation = run.getProperty('polarisation').value
            logger.debug(str(angle))
            logger.debug(str(flipper))
            logger.debug(str(polarisation))
            #if 'vana' in ws[0] or 'nicr' in ws[0] or 'leer' in ws[0]:
            for key in deterota:
                logger.debug(str(key))
                logger.debug(str(angle))
                logger.debug(str(np.fabs(angle-key)))
                logger.debug(str(self.tol))
                logger.debug(str(np.fabs(angle-key) < float(self.tol)))
                if np.fabs(angle - key) < self.tol:
                    angle = key
            logger.debug(str(angle))
            print(wsname)
            if flipper == 'ON':
                if polarisation == 'x':
                    print('in flip = on and x (x_sf)')
                    if angle in x_sf.keys() and bool(x_sf[angle]):
                        self._sum_same(ws, x_sf, angle, wsname)
                        print("Double angle. list: " + str(x_sf) + " angle: " + str(angle))
                    else:
                        x_sf[angle] = wsname
                elif polarisation == 'y':
                    print('in flip = on and y (y_sf)')
                    if angle in y_sf.keys() and bool(y_sf[angle]):
                        print("Double angle. list: " + str(y_sf) + " angle: " + str(angle))
                        self._sum_same(ws, y_sf, angle, wsname)
                    else:
                        y_sf[angle] = wsname
                else:
                    print('in flip = on and z (z_sf)')
                    if angle in z_sf.keys() and bool(z_sf[angle]):
                        print("Double angle. list: " + str(z_sf) + " angle: " + str(angle))
                        self._sum_same(ws, z_sf, angle, wsname)
                    else:
                        z_sf[angle] = wsname
            else:
                if polarisation == 'x':
                    print("in flip = off an x (x_nsf)")
                    if angle in x_nsf.keys() and bool(x_nsf[angle]):
                        print("Double angle. List: " + str(x_nsf) + " angle: " + str(angle) + " old ws " + str(x_nsf[angle]))
                        self._sum_same(ws, x_nsf, angle, wsname)
                    else:
                        x_nsf[angle] = wsname
                elif polarisation == 'y':
                    print("in flip = off and y (y_nsf)")
                    if angle in y_nsf.keys() and bool(y_nsf[angle]):
                        print("Double angle. list: " + str(y_nsf) + " angle: " + str(angle))
                        self._sum_same(ws, y_nsf, angle, wsname)
                    else:
                        y_nsf[angle] = wsname
                else:
                    print("in flip = off and z (z_nsf)")
                    if angle in z_nsf.keys() and bool(z_nsf[angle]):
                        print("Double angle. list: " + str(z_nsf) + " angle: " + str(angle))
                        self._sum_same(ws, z_nsf, angle, wsname)
                    else:
                        z_nsf[angle] = wsname

        x_sf = OrderedDict(sorted(x_sf.items()))
        x_nsf = OrderedDict(sorted(x_nsf.items()))
        y_sf = OrderedDict(sorted(y_sf.items()))
        y_nsf = OrderedDict(sorted(y_nsf.items()))
        z_sf = OrderedDict(sorted(z_sf.items()))
        z_nsf = OrderedDict(sorted(z_nsf.items()))
        logger.debug(str(x_sf))
        logger.debug(str(x_nsf))
        logger.debug(str(y_sf))
        logger.debug(str(y_nsf))
        logger.debug(str(z_sf))
        logger.debug(str(z_nsf))
        self._out_ws_name = self.getProperty('OutWorkspaceName').value
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

            logger.debug(str(group_names))
            self._use_ws = []
            for var in group_names:
                gname = var + '_group'
                logger.debug(gname)
                ws_n = var[-5:]
                if ws_n[0] == '_':
                    ws_n = ws_n[1:]
                logger.debug(ws_n)
                wsp = eval(ws_n).values()
                logger.debug(str(wsp))
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
                    self._extract_norm_workspace(mtd[gname], self._norm)
                    if self._m_and_n:
                        self._merge_and_normalize(gname, self.xax)

        else:
            self._use_ws = []

    def PyExec(self):

        self.xax = self.getProperty('XAxisUnit').value
        logger.debug(str(self.xax))

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self._instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self._suff_norm = self._instrument.getStringParameter("normws_suffix")[0]

        self.tol = float(self._instrument.getStringParameter("two_theta_tolerance")[0])

        self._m_and_n = self._instrument.getBoolParameter("keep_intermediate_workspace")[0]
        self._norm = self.getProperty('Normalization').value
        logger.debug("norm: " + str(self._norm))

        if self.getProperty('FilesList').value:
            self._load_ws_sample()
        else:
            self._load_ws_standard()
        logs = ['run_title', 'polarisation', 'flipper', 'deterota']
        table_name = self._out_ws_name + '_' + self.getProperty('OutputTable').value
        if self._use_ws:
            logger.debug(str(self._use_ws))

            CreateLogPropertyTable(self._use_ws, OutputWorkspace=table_name, LogPropertyNames=logs, GroupPolicy='All')


AlgorithmFactory.subscribe(DNSLoadData)
