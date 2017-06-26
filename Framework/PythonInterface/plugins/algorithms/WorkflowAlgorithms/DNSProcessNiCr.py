from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import logger
from mantid.simpleapi import LoadEmptyInstrument, DeleteWorkspace, Divide, Multiply, Minus, \
    CloneWorkspace, DNSMergeRuns, Scale, AddSampleLog

import numpy as np


class DNSProcessNiCr(PythonAlgorithm):

    def _merge_and_normalize(self, wsgroup, xax, namex= ''):
        xaxis = xax.split(', ')
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
        self.declareProperty(name='NiCrTable', defaultValue='', doc='Name of the nickel-chrome ITableWorkspace')
        self.declareProperty(name='SampleTable', defaultValue='', doc='Name of the sample data ITableWorkspace')
        self.declareProperty(name='OutputWorkspace', defaultValue='', doc='Name of the output workspace')
        self.declareProperty(name='XAxisUnits', defaultValue='', doc='List of the output x axis units')
        self.declareProperty(name='DetEffiCorrection', defaultValue='',
                             doc='Bool, true if the detector efficiency should be corrected')
        self.declareProperty(name='FlippCorrFactor', defaultValue='',
                             doc='Factor for the flipping ratio correction')

    def PyExec(self):

        self.nicr_table = mtd[self.getProperty('NiCrTable').value]
        self.sample_table = mtd[self.getProperty('SampleTable').value]
        self.out_ws_name = self.getProperty('OutputWorkspace').value
        self.xax = self.getProperty('XAxisUnits').value
        self.detEffi = self.getProperty('DetEffiCorrection').value
        self.flippFac = self.getProperty('FlippCorrFactor').value

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self.instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm = self.instrument.getStringParameter('normws_suffix')[0]
        self.tol = float(self.instrument.getStringParameter('two_theta_tolerance')[0])

        logger.debug(self.nicr_table.getName())
        logger.debug(self.sample_table.getName())

        new_sample_table = self.sample_table.clone(OutputWorkspace=self.out_ws_name+'_SampleTableNiCrCoef')
        new_sample_table.addColumn('str', 'nicr_coef')
        new_sample_table.addColumn('str', 'nicr_coef_group')

        self.offset = 0
        gr1 = self.nicr_table.cell('ws_group', 0)
        gr2 = self.nicr_table.cell('ws_group', self.offset)

        while gr1 == gr2:
            self.offset += 1
            gr2 = self.nicr_table.cell('ws_group', self.offset)

        row = 0
        nicr_coefs_dict = {}

        while row < self.nicr_table.rowCount():

            pol = self.nicr_table.cell('polarisation', row)
            nicr_group_sf = self.nicr_table.cell('ws_group', row)
            bkg_group_sf = nicr_group_sf.replace('rawnicr', 'leer')

            logger.debug('nicr group: ' + nicr_group_sf + ', bkg group: ' + bkg_group_sf + ', pol: ' + pol)

            row += self.offset

            nicr_group_nsf = self.nicr_table.cell('ws_group', row)
            bkg_group_nsf = nicr_group_nsf.replace('rawnicr', 'leer')

            logger.debug('nicr group: ' + nicr_group_nsf + ', bkg group: ' + bkg_group_nsf + ', pol: ' + pol)

            row += self.offset

            norm_ratio_sf = Divide(nicr_group_sf+self.suff_norm, bkg_group_sf+self.suff_norm,
                                   OutputWorkspace=nicr_group_sf+'_nratio')
            norm_ratio_nsf = Divide(nicr_group_nsf+self.suff_norm, bkg_group_nsf+self.suff_norm,
                                    OutputWorkspace=nicr_group_nsf+'_nratio')

            leer_scaled_sf = Multiply(bkg_group_sf, norm_ratio_sf,
                                      OutputWorkspace=bkg_group_sf.replace('group', 'nicr'))
            leer_scaled_nsf = Multiply(bkg_group_nsf, norm_ratio_nsf,
                                       OutputWorkspace=bkg_group_nsf.replace('group', 'nicr'))

            Minus(nicr_group_sf, leer_scaled_sf, OutputWorkspace=nicr_group_sf.replace('raw', ''))
            CloneWorkspace(nicr_group_sf+self.suff_norm,
                           OutputWorkspace=nicr_group_sf.replace('raw', '')+self.suff_norm)

            Minus(nicr_group_nsf, leer_scaled_nsf, OutputWorkspace=nicr_group_nsf.replace('raw', ''))
            CloneWorkspace(nicr_group_nsf+self.suff_norm,
                           OutputWorkspace=nicr_group_nsf.replace('raw', '')+self.suff_norm)

            nicr_group_sf = nicr_group_sf.replace('raw', '')
            nicr_group_nsf = nicr_group_nsf.replace('raw', '')

            self._merge_and_normalize(nicr_group_sf, self.xax)
            self._merge_and_normalize(nicr_group_nsf, self.xax)

            nicr_nratio = Divide(nicr_group_nsf+self.suff_norm, nicr_group_sf+self.suff_norm,
                                 OutputWorkspace=nicr_group_nsf.replace('group', 'nratio'))
            nicr_coefs_norm = Multiply(nicr_group_sf, nicr_nratio,
                                       OutputWorkspace=nicr_group_sf.replace('group', 'scaled'))

            nicr_coefs = Minus(nicr_group_nsf, nicr_coefs_norm, OutputWorkspace='nicr_coefs_'+pol)

            #nicr_coefs_normalized = nicr_coefs/nicr_coefs_norm
            nicr_coefs_normalized = Divide(nicr_coefs, nicr_coefs_norm, OutputWorkspace='nicr_coefs_normalized_'+pol)
            AddSampleLog(nicr_coefs_normalized, LogName='ws_group', LogText=nicr_coefs_normalized.getName())
            dete_dict = {}

            for coefs_ws in nicr_coefs_normalized:
                logger.debug(str(coefs_ws.getRun().getProperty('deterota').value))
                dete_dict[coefs_ws.getRun().getProperty('deterota').value] = coefs_ws.getName()

            nicr_coefs_dict[pol] = dete_dict

        for i in range(new_sample_table.rowCount()):
            row = new_sample_table.row(i)
            pol = row['polarisation']
            angle = float(row['deterota'])
            for key in nicr_coefs_dict[pol].keys():
                if np.fabs(angle - key) < self.tol:
                    angle = key
            new_sample_table.setCell('nicr_coef', i, nicr_coefs_dict[pol][angle])
            new_sample_table.setCell('nicr_coef_group', i,
                                     mtd[nicr_coefs_dict[pol][angle]].getRun().getProperty('ws_group').value)
            print(str(row))

AlgorithmFactory.subscribe(DNSProcessNiCr)
