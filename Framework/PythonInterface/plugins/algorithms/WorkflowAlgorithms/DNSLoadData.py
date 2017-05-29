from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import logger
from mantid.simpleapi import LoadDNSLegacy

import numpy as np

import os

class DNSLoadData(PythonAlgorithm):

    def category(self):
        return "Workflow"

    def PyInit(self):

        self.declareProperty(name='FilesList', defaultValue='',
                             doc='List of files of the Data you want to load')
        self.declareProperty(name='DataPath', defaultValue='', doc='Path to the files')
        self.tol = 0.05

    def is_in_list(self, angle_list, angle, tolerance):
        for a in angle_list:
            if np.fabs(a - angle) < tolerance:
                 return True
        return False

    def _load_ws(self):

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
            if flipper == 'ON':
                if polarisation == 'x':
                    x_sf[angle] = wsname
                elif polarisation == 'y':
                    y_sf[angle] = wsname
                else:
                    z_sf[angle] = wsname
            else:
                if polarisation == 'x':
                    x_nsf[angle] = wsname
                elif polarisation == 'y':
                    y_nsf[angle] = wsname
                else:
                    z_nsf[angle] = wsname
        logger.debug(str(x_sf))
        logger.debug(str(x_nsf))
        logger.debug(str(y_sf))
        logger.debug(str(y_nsf))
        logger.debug(str(z_sf))
        logger.debug(str(z_nsf))

    def PyExec(self):

        self._load_ws()


AlgorithmFactory.subscribe(DNSLoadData)
