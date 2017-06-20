from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, ITableWorkspace, ITableWorkspaceProperty, mtd
from mantid.kernel import logger, Direction
from mantid.simpleapi import CreateEmptyTableWorkspace, Minus, CloneWorkspace, Divide, LoadEmptyInstrument, \
    DeleteWorkspace, Multiply, DNSMergeRuns
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
        self.declareProperty(name='OutWorkspaceName', defaultValue='', doc='')
        self.declareProperty(name='SubtractBackground', defaultValue='', doc='')
        self.declareProperty(name='XAxisUnits', defaultValue='')

    def PyExec(self):

        tables = []
        columnames = {}
        columgroupname = {}
        ws_name = self.getProperty('OutWorkspaceName').value
        sample = mtd[self.getProperty('SampleTable').value]
        nicr_name = self.getProperty('NiCrTable').value
        leer_name = self.getProperty('BackgroundTable').value
        self.xax = self.getProperty('XAxisUnits').value
        print(self.xax)

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self.instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)
        self.suff_norm = self.instrument.getStringParameter('normws_suffix')[0]

        if mtd.doesExist(nicr_name):
            print('nicr')
            nicr = mtd[nicr_name]
            tables.append(nicr)
            columnames[nicr.getName()] = 'nicr_ws'
            columgroupname[nicr.getName()] = 'nicr_group_ws'
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
        tableWs.addColumn('str', 'nicr_ws')
        tableWs.addColumn('str', 'nicr_group_ws')

        for i in range(len(tableWs.column(0))):
            row_out = tableWs.row(i)
            for t in tables:
                for j in range(len(t.column(0))):
                    row = t.row(j)
                    if row_out['polarisation'] == row['polarisation']:
                        if row_out['flipper'] == row['flipper']:
                            if np.abs(float(row_out['deterota'])-float(row['deterota'])) < 0.5:
                                tableWs.setCell(columnames[t.getName()], i, row['run_title'])
                                tableWs.setCell(columgroupname[t.getName()], i, row['ws_group'])

        norm_ratio = {}
        leer_scaled = {}
        """for p in ['_x', '_y', '_z']:
            for flip in ['_sf', '_nsf']:
                inws = ws_name+'_rawdata'+p+flip+'_group'
                bkgws = ws_name+'_leer'+p+flip+'_group'
                if mtd.doesExist(inws):
                    if self.getProperty('SubtractBackground').value:
                        print('Sub bkg. data: ', inws, ' bkg: ', bkgws)
                        norm_ratio[p+flip] = Divide(inws+self.suff_norm, bkgws+self.suff_norm,
                                                    OutputWorkspace=ws_name+'_rawdata'+p+flip+'_nratio')
                        leer_scaled[p+flip] = Multiply(bkgws, norm_ratio[p+flip],
                                                       OutputWorkspace=ws_name+'_leer'+p+flip+'_rawdata')
                        Minus(inws, leer_scaled[p+flip], OutputWorkspace=ws_name+'_data'+p+flip+'_group')
                        CloneWorkspace(inws+self.suff_norm, OutputWorkspace=ws_name+'_data'+p+flip+'_group'+self.suff_norm)
                        self._merge_and_normalize(ws_name+'_data'+p+flip+'_group', self.xax)
                        #bkgws = ws_name+'_leer'+p+flip+'_group'
                        #resws = ws_name+'_data'+p+flip+'_group'
                        #Minus(inws,bkgws,OutputWorkspace=resws)
                    else:
                        CloneWorkspace(inws, ws_name+'_data'+p+flip+'_group')"""





AlgorithmFactory.subscribe(DNSProcessStandardData)
