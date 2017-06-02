from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, ITableWorkspace, ITableWorkspaceProperty, mtd
from mantid.kernel import logger, Direction
from mantid.simpleapi import CreateEmptyTableWorkspace
import numpy as np


class DNSProcessStandardData(PythonAlgorithm):

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name='SampleTable', defaultValue='', doc='Table of sample Data')
        self.declareProperty(name='NiCrTable', defaultValue='', doc='Table of nicr Data')
        self.declareProperty(name='BackgroundTable', defaultValue='', doc='Table of background Data')
        self.declareProperty(name='OutputTable', defaultValue='', doc='Name of the output table')
        self.declareProperty(name='OutWorkspaceName', defaultValue='')

    def PyExec(self):

        tables = []
        columnames = {}
        ws_name = self.getProperty('OutWorkspaceName').value
        sample = mtd[self.getProperty('SampleTable').value]
        nicr_name = self.getProperty('NiCrTable').value
        leer_name = self.getProperty('BackgroundTable').value
        if mtd.doesExist(nicr_name):
            print('nicr')
            nicr = mtd[nicr_name]
            tables.append(nicr)
            columnames[nicr.getName()] = 'Nicr ws'
        if mtd.doesExist(leer_name):
            print('leer')
            leer = mtd[leer_name]
            tables.append(leer)
            columnames[leer.getName()] = 'Background ws'
        out_table_name = ws_name + '_' + self.getProperty('OutputTable').value
        logger.debug(sample.getName())

        tableWs = sample.clone(OutputWorkspace=out_table_name)
        logger.debug(tableWs.getName())

        tableWs.addColumn('str', 'Background ws')
        tableWs.addColumn('str', 'Nicr ws')

        for i in range(len(tableWs.column(0))):
            row_out = tableWs.row(i)
            for t in tables:
                for j in range(len(t.column(0))):
                    row = t.row(j)
                    if row_out['polarisation'] == row['polarisation']:
                        if row_out['flipper'] == row['flipper']:
                            if np.abs(float(row_out['deterota'])-float(row['deterota'])) < 0.5:
                                tableWs.setCell(columnames[t.getName()], i, row['run_title'])





AlgorithmFactory.subscribe(DNSProcessStandardData)
