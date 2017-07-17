from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd

import numpy as np


class DNSProcessStandardData(PythonAlgorithm):

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name='SampleTable',     defaultValue='', doc='Table of sample Data')
        self.declareProperty(name='NiCrTable',       defaultValue='', doc='Table of nicr Data')
        self.declareProperty(name='BackgroundTable', defaultValue='', doc='Table of background Data')
        self.declareProperty(name='OutputTable',     defaultValue='', doc='Name of the output table')
        self.declareProperty(name='OutputWorkspace', defaultValue='', doc='Name of the output workspace')

    def PyExec(self):

        tables = []
        column_names = {}
        column_group_name = {}

        ws_name        = self.getProperty('OutputWorkspace').value
        leer_name      = self.getProperty('BackgroundTable').value
        out_table_name = ws_name+'_'+self.getProperty('OutputTable').value

        sample_table = mtd[self.getProperty('SampleTable').value]

        if mtd.doesExist(leer_name):
            leer = mtd[leer_name]
            tables.append(leer)
            column_names[leer.getName()] = 'background_ws'
            column_group_name[leer.getName()] = 'background_group_ws'

        tableWs = sample_table.clone(OutputWorkspace=out_table_name)

        tableWs.addColumn('str', 'background_ws')
        tableWs.addColumn('str', 'background_group_ws')

        for i in range(tableWs.rowCount()):
            row_out = tableWs.row(i)
            for t in tables:
                for j in range(t.rowCount()):
                    row = t.row(j)
                    if row_out['polarisation'] == row['polarisation']:
                        if row_out['flipper'] == row['flipper']:
                            if np.abs(float(row_out['deterota'])-float(row['deterota'])) < 0.5:
                                tableWs.setCell(column_names[t.getName()], i, row['run_title'])
                                tableWs.setCell(column_group_name[t.getName()], i, row['ws_group'])

AlgorithmFactory.subscribe(DNSProcessStandardData)
