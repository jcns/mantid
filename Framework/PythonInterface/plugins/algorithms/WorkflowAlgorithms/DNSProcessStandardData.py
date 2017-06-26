from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import logger
from mantid.simpleapi import Divide, LoadEmptyInstrument, \
    DeleteWorkspace, DNSMergeRuns
import numpy as np


class DNSProcessStandardData(PythonAlgorithm):

    def _merge_and_normalize(self, wsgroup, xax, namex=''):
        print(xax)
        xaxis = xax.split(', ')
        print(str(xaxis))
        for x in xaxis:
            data_merged = DNSMergeRuns(wsgroup + namex, x, OutputWorkspace=wsgroup + '_m0' + '_' + x)
            norm_merged = DNSMergeRuns(wsgroup + self.suff_norm + namex, x,
                                       OutputWorkspace=wsgroup + self.suff_norm +'_m' + '_' + x)
            try:
                Divide(data_merged, norm_merged, OutputWorkspace=wsgroup + '_m' + '_' + x)
            except:
                dataX = data_merged.extractX()
                norm_merged.setX(0, dataX[0])
                Divide(data_merged, norm_merged, OutputWorkspace=wsgroup+'_m' + '_' + x)

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name='SampleTable', defaultValue='', doc='Table of sample Data')
        self.declareProperty(name='NiCrTable', defaultValue='', doc='Table of nicr Data')
        self.declareProperty(name='BackgroundTable', defaultValue='', doc='Table of background Data')
        self.declareProperty(name='OutputTable', defaultValue='', doc='Name of the output table')
        self.declareProperty(name='OutputWorkspace', defaultValue='', doc='Name of the output workspace')
        self.declareProperty(name='XAxisUnits', defaultValue='Units for the output x axis')

    def PyExec(self):

        tables = []
        columnames = {}
        columgroupname = {}
        ws_name = self.getProperty('OutputWorkspace').value
        sample = mtd[self.getProperty('SampleTable').value]
        #nicr_name = self.getProperty('NiCrTable').value
        leer_name = self.getProperty('BackgroundTable').value
        self.xax = self.getProperty('XAxisUnits').value
        print(self.xax)

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self.instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)
        self.suff_norm = self.instrument.getStringParameter('normws_suffix')[0]

        #if mtd.doesExist(nicr_name):
        #    print('nicr')
        #    nicr = mtd[nicr_name]
        #    tables.append(nicr)
        #    columnames[nicr.getName()] = 'nicr_ws'
        #    columgroupname[nicr.getName()] = 'nicr_group_ws'
        if mtd.doesExist(leer_name):
            print('leer')
            leer = mtd[leer_name]
            tables.append(leer)
            columnames[leer.getName()] = 'background_ws'
            columgroupname[leer.getName()] = 'background_group_ws'
        out_table_name = ws_name + '_' + self.getProperty('OutputTable').value
        logger.debug(sample.getName())

        tableWs = sample.clone(OutputWorkspace=out_table_name)
        logger.debug(tableWs.getName())

        tableWs.addColumn('str', 'background_ws')
        tableWs.addColumn('str', 'background_group_ws')
        #tableWs.addColumn('str', 'nicr_ws')
        #tableWs.addColumn('str', 'nicr_group_ws')

        for i in range(tableWs.rowCount()):
            row_out = tableWs.row(i)
            for t in tables:
                for j in range(t.rowCount()):
                    row = t.row(j)
                    if row_out['polarisation'] == row['polarisation']:
                        if row_out['flipper'] == row['flipper']:
                            if np.abs(float(row_out['deterota'])-float(row['deterota'])) < 0.5:
                                tableWs.setCell(columnames[t.getName()], i, row['run_title'])
                                tableWs.setCell(columgroupname[t.getName()], i, row['ws_group'])

AlgorithmFactory.subscribe(DNSProcessStandardData)
