from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import logger
from mantid.simpleapi import Plus, Divide, SumSpectra, Mean, DNSMergeRuns,\
    CloneWorkspace, LoadEmptyInstrument, DeleteWorkspace, Multiply, Minus, AddSampleLog

import numpy as np


class DNSProcessVanadium(PythonAlgorithm):

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

        self.declareProperty(name='VanadiumTable', defaultValue='', doc='Name of the vanadium ITableWorkspace')
        self.declareProperty(name='BackgroundTable', defaultValue='', doc='Name of the background ITableWorkspace ')
        self.declareProperty(name='SampleTable', defaultValue='', doc='Name of the sample data ITableWorkspace')
        self.declareProperty(name='OutputWorkspace', defaultValue='Name for the output Workspace')
        self.declareProperty(name='OutputXAxis', defaultValue='', doc='List of the output x axis units')
        self.declareProperty(name='Normalization', defaultValue='', doc='Type of normalization')

    def PyExec(self):

        self.vana_table = mtd[self.getProperty('VanadiumTable').value]
        self.bkg_table = mtd[self.getProperty('BackgroundTable').value]
        self.sample_table = mtd[self.getProperty('SampleTable').value]
        out_ws_name = self.getProperty('OutputWorkspace').value

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self.instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm = self.instrument.getStringParameter('normws_suffix')[0]
        self.tol = float(self.instrument.getStringParameter('two_theta_tolerance')[0])

        logger.debug(self.vana_table.getName())
        logger.debug(self.bkg_table.getName())
        logger.debug(self.sample_table.getName())

        self.offset = 0
        gr = self.vana_table.cell('ws_group', 0)
        gr2 = self.vana_table.cell('ws_group', self.offset)
        while gr == gr2:
            self.offset += 1
            gr2 = self.vana_table.cell('ws_group', self.offset)

        self.xax = self.getProperty('OutputXAxis').value

        new_sample_table = self.sample_table.clone(OutputWorkspace= out_ws_name + '_SampleTableVanaCoef')

        logger.debug(str(self.offset))

        new_sample_table.addColumn('str', 'vana_coef')
        new_sample_table.addColumn('str', 'vana_coef_group')

        if self.vana_table.rowCount() == self.sample_table.rowCount() \
                and self.bkg_table.rowCount() == self.vana_table.rowCount():

            row = 0
            vana_coefs_dict = {}

            while row < self.vana_table.rowCount():

                print("while, row: ", row)

                vana_group_sf = self.vana_table.cell('ws_group', row)
                pol = self.vana_table.cell('polarisation', row)
                bkg_group_sf = vana_group_sf.replace("rawvana", "leer", 1)

                print('vana group: ', vana_group_sf, ", bkg group: ", bkg_group_sf)

                row = row+self.offset

                vana_group_nsf = self.vana_table.cell('ws_group', row)
                bkg_group_nsf = vana_group_nsf.replace("rawvana", "leer", 1)

                print('vana group: ', vana_group_nsf, ", bkg group: ", bkg_group_nsf)

                row = row+self.offset

                norm_ratio_sf = Divide(vana_group_sf+self.suff_norm, bkg_group_sf+self.suff_norm,
                                       OutputWorkspace=vana_group_sf+'_nratio')
                norm_ratio_nsf = Divide(vana_group_nsf+self.suff_norm, bkg_group_nsf+self.suff_norm,
                                        OutputWorkspace=vana_group_nsf+'_nratio')

                leer_scaled_sf = Multiply(bkg_group_sf, norm_ratio_sf,
                                          OutputWorkspace=bkg_group_sf.replace('group', 'vana'))

                leer_scaled_nsf = Multiply(bkg_group_nsf, norm_ratio_nsf,
                                           OutputWorkspace=bkg_group_nsf.replace('group', 'vana'))

                Minus(vana_group_sf, leer_scaled_sf, OutputWorkspace=vana_group_sf.replace('raw', ''))
                CloneWorkspace(vana_group_sf+self.suff_norm,
                               OutputWorkspace=vana_group_sf.replace('raw', '')+self.suff_norm)

                Minus(vana_group_nsf, leer_scaled_nsf, OutputWorkspace=vana_group_nsf.replace('raw', ''))
                CloneWorkspace(vana_group_nsf+self.suff_norm,
                               OutputWorkspace=vana_group_nsf.replace('raw', '')+self.suff_norm)

                vana_group_sf = vana_group_sf.replace('raw', '')
                vana_group_nsf = vana_group_nsf.replace('raw', '')

                self._merge_and_normalize(vana_group_sf, self.xax)
                self._merge_and_normalize(vana_group_nsf, self.xax)

                vana_sf_nsf_sum = Plus(vana_group_sf, vana_group_nsf, OutputWorkspace='vana_sf_nsf_sum_'+pol)
                vana_sf_nsf_sum_norm = Plus(vana_group_sf+self.suff_norm, vana_group_nsf+self.suff_norm,
                                            OutputWorkspace='vana_sf_nsf_sum_norm_'+pol)

                vana_total = SumSpectra(vana_sf_nsf_sum, OutputWorkspace='vana_total_'+pol)
                vana_total_norm = SumSpectra(vana_sf_nsf_sum_norm, OutputWorkspace='vana_total_norm_'+pol)

                vana_mean = Mean(', '.join(vana_total.getNames()), OutputWorkspace='vana_mean_'+pol)
                vana_mean_norm = Mean(', '.join(vana_total_norm.getNames()), OutputWorkspace='vana_mean_norm_'+pol)

                #vana_coefs = vana_sf_nsf_sum/vana_mean
                #vana_coefs_norm = vana_sf_nsf_sum_norm/vana_mean_norm
                vana_coefs = Divide(vana_sf_nsf_sum, vana_mean, OutputWorkspace='vana_coefs_'+pol)
                vana_coefs_norm = Divide(vana_sf_nsf_sum_norm, vana_mean_norm, OutputWorkspace='vana_coefs_norm_'+pol)

                #vana_coefs_total = vana_coefs/vana_coefs_norm
                vana_coefs_total = Divide(vana_coefs, vana_coefs_norm, OutputWorkspace='vana_coefs_total_'+pol)

                AddSampleLog(vana_coefs_total, LogName='ws_group', LogText=vana_coefs_total.getName())

                deterota = []
                dete_dict = {}

                for coef_ws in vana_coefs_total:
                    logger.debug(str(coef_ws.getRun().getProperty('deterota').value))
                    deterota.append(coef_ws.getRun().getProperty('deterota').value)
                    dete_dict[coef_ws.getRun().getProperty('deterota').value] = coef_ws.getName()

                vana_coefs_dict[pol] = dete_dict

            for i in range(new_sample_table.rowCount()):
                row = new_sample_table.row(i)
                pol = row['polarisation']
                angle = float(row['deterota'])
                for key in vana_coefs_dict[pol].keys():
                    if np.fabs(angle - key) < self.tol:
                        angle = key
                new_sample_table.setCell('vana_coef', i, vana_coefs_dict[pol][angle])
                new_sample_table.setCell('vana_coef_group', i,
                                         mtd[vana_coefs_dict[pol][angle]].getRun().getProperty('ws_group').value)
                print(str(row))

        elif self.sample_table.rowCount()/3 == self.vana_table.rowCount() \
                or self.bkg_table.rowCount()/3 == self.vana_table.rowCount():

            row = 0

            while row < self.vana_table.rowCount():

                print("while, row: ", row)

                vana_group_sf = self.vana_table.cell('ws_group', row)
                bkg_group_sf = vana_group_sf.replace("rawvana", "leer", 1)

                print('vana group: ', vana_group_sf, ", bkg group: ", bkg_group_sf)

                row = row+self.offset

                vana_group_nsf = self.vana_table.cell('ws_group', row)
                bkg_group_nsf = vana_group_nsf.replace("rawvana", "leer", 1)

                print('vana group: ', vana_group_nsf, ", bkg group: ", bkg_group_nsf)

                row = row+self.offset

                norm_ratio_sf = Divide(vana_group_sf+self.suff_norm, bkg_group_sf+self.suff_norm,
                                       OutputWorkspace=vana_group_sf+'_nratio')
                norm_ratio_nsf = Divide(vana_group_nsf+self.suff_norm, bkg_group_nsf+self.suff_norm,
                                        OutputWorkspace=vana_group_nsf+'_nratio')

                leer_scaled_sf = Multiply(bkg_group_sf, norm_ratio_sf,
                                          OutputWorkspace=bkg_group_sf.replace('group', 'vana'))

                leer_scaled_nsf = Multiply(bkg_group_nsf, norm_ratio_nsf,
                                           OutputWorkspace=bkg_group_nsf.replace('group', 'vana'))

                Minus(vana_group_sf, leer_scaled_sf, OutputWorkspace=vana_group_sf.replace('raw', ''))
                CloneWorkspace(vana_group_sf+self.suff_norm,
                               OutputWorkspace=vana_group_sf.replace('raw', '')+self.suff_norm)

                Minus(vana_group_nsf, leer_scaled_nsf, OutputWorkspace=vana_group_nsf.replace('raw', ''))
                CloneWorkspace(vana_group_nsf+self.suff_norm,
                               OutputWorkspace=vana_group_nsf.replace('raw', '')+self.suff_norm)

                vana_group_sf = vana_group_sf.replace('raw', '')
                vana_group_nsf = vana_group_nsf.replace('raw', '')

                self._merge_and_normalize(vana_group_sf, self.xax)
                self._merge_and_normalize(vana_group_nsf, self.xax)

                vana_sf_nsf_sum = Plus(vana_group_sf, vana_group_nsf)
                vana_sf_nsf_sum_norm = Plus(vana_group_sf+self.suff_norm, vana_group_nsf+self.suff_norm)

                vana_total = SumSpectra(vana_sf_nsf_sum)
                vana_total_norm = SumSpectra(vana_sf_nsf_sum_norm)

                vana_mean = Mean(', '.join(vana_total.getNames()))
                vana_mean_norm = Mean(', '.join(vana_total_norm.getNames()))

                vana_coefs = vana_sf_nsf_sum/vana_mean
                vana_coefs_norm = vana_sf_nsf_sum_norm/vana_mean_norm

                vana_coefs_total = vana_coefs/vana_coefs_norm

                vana_coefs_dict = {}

                deterota = []

                for coef_ws in vana_coefs_total:
                    logger.debug(str(coef_ws.getRun().getProperty('deterota').value))
                    deterota.append(coef_ws.getRun().getProperty('deterota').value)
                    vana_coefs_dict[coef_ws.getRun().getProperty('deterota').value] = coef_ws.getName()

                for i in range(new_sample_table.rowCount()):
                    row = new_sample_table.row(i)
                    angle = float(row['deterota'])
                    for key in deterota:
                        if np.fabs(angle - key) < self.tol:
                            angle = key
                    new_sample_table.setCell('vana_coef', i, vana_coefs_dict[angle])
                    new_sample_table.setCell('vana_coef_group', i , vana_coefs_total.getName())
                    print(str(row))

AlgorithmFactory.subscribe(DNSProcessVanadium)
