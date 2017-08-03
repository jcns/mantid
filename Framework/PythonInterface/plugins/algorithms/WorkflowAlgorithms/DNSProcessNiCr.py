from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.simpleapi import LoadEmptyInstrument, DeleteWorkspace, Divide, Multiply, Minus, \
    CloneWorkspace, DNSMergeRuns, Scale, AddSampleLog

import numpy as np


class DNSProcessNiCr(PythonAlgorithm):

    def _merge_and_normalize(self, ws_group):

        x_axis = self.xax.split(', ')
        for x in x_axis:
            data_merged = DNSMergeRuns(ws_group, x, OutputWorkspace=ws_group+'_m0'+'_'+x)
            norm_merged = DNSMergeRuns(ws_group+self.suff_norm, x, OutputWorkspace=ws_group+self.suff_norm+'_m'+'_'+x)
            try:
                Divide(data_merged, norm_merged, OutputWorkspace=ws_group+'_m'+'_'+x)
            except:
                data_x = data_merged.extractX()
                norm_merged.setX(0, data_x[0])
                Divide(data_merged, norm_merged, OutputWorkspace=ws_group+'_m'+'_'+x)

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name='SampleTable',     defaultValue='', doc='Name of the sample data ITableWorkspace')
        self.declareProperty(name='NiCrTable',       defaultValue='', doc='Name of the nickel-chrome ITableWorkspace')
        self.declareProperty(name='OutputWorkspace', defaultValue='', doc='Name of the output workspace')
        self.declareProperty(name='XAxisUnits',      defaultValue='', doc='List of the output x axis units')
        self.declareProperty(name='Polarisations',   defaultValue='', doc='')
        self.declareProperty(name='FlippCorrFactor', defaultValue='', doc='Factor for the flipping ratio correction')
        self.declareProperty(name='SingleCrystal',   defaultValue='', doc='')

    def PyExec(self):

        sample_table = mtd[self.getProperty('SampleTable').value]
        nicr_table   = mtd[self.getProperty('NiCrTable').value]

        out_ws_name = self.getProperty('OutputWorkspace').value
        self.xax         = self.getProperty('XAxisUnits').value

        polarisations = self.getProperty('Polarisations').value.split(', ')

        flippFac = self.getProperty('FlippCorrFactor').value

        sc      = self.getProperty('SingleCrystal').value
        self.sc = eval(sc)

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm = instrument.getStringParameter('normws_suffix')[0]
        tol            = float(instrument.getStringParameter('two_theta_tolerance')[0])
        self._m_and_n  = instrument.getBoolParameter('keep_intermediate_workspace')[0]

        new_sample_table = sample_table.clone(OutputWorkspace=out_ws_name+'_SampleTableNiCrCoef')
        new_sample_table.addColumn('str', 'nicr_coef')
        new_sample_table.addColumn('str', 'nicr_coef_group')

        offset = 0
        gr1 = nicr_table.cell('ws_group', 0)
        gr2 = nicr_table.cell('ws_group', offset)

        while gr1 == gr2:
            offset += 1
            gr2 = nicr_table.cell('ws_group', offset)

        row = 0
        nicr_coefs_dict = {}

        while row < nicr_table.rowCount():

            pol = nicr_table.cell('polarisation', row)

            nicr_group_sf = nicr_table.cell('ws_group', row)
            bkg_group_sf  = nicr_group_sf.replace('rawnicr', 'leer')

            row += offset

            nicr_group_nsf = nicr_table.cell('ws_group', row)
            bkg_group_nsf  = nicr_group_nsf.replace('rawnicr', 'leer')

            row += offset

            if pol in polarisations:

                norm_ratio_sf  = Divide(nicr_group_sf+self.suff_norm, bkg_group_sf+self.suff_norm,
                                        OutputWorkspace=nicr_group_sf+'_nratio')
                norm_ratio_nsf = Divide(nicr_group_nsf+self.suff_norm, bkg_group_nsf+self.suff_norm,
                                        OutputWorkspace=nicr_group_nsf+'_nratio')

                leer_scaled_sf  = Multiply(bkg_group_sf, norm_ratio_sf,
                                           OutputWorkspace=bkg_group_sf.replace('group', 'nicr'))
                leer_scaled_nsf = Multiply(bkg_group_nsf, norm_ratio_nsf,
                                           OutputWorkspace=bkg_group_nsf.replace('group', 'nicr'))

                Minus(nicr_group_sf, leer_scaled_sf, OutputWorkspace=nicr_group_sf.replace('raw', ''))
                CloneWorkspace(nicr_group_sf+self.suff_norm,
                               OutputWorkspace=nicr_group_sf.replace('raw', '')+self.suff_norm)

                Minus(nicr_group_nsf, leer_scaled_nsf, OutputWorkspace=nicr_group_nsf.replace('raw', ''))
                CloneWorkspace(nicr_group_nsf+self.suff_norm,
                               OutputWorkspace=nicr_group_nsf.replace('raw', '')+self.suff_norm)

                nicr_group_sf  = nicr_group_sf.replace('raw', '')
                nicr_group_nsf = nicr_group_nsf.replace('raw', '')

                if self._m_and_n and not self.sc:
                    self._merge_and_normalize(nicr_group_sf)
                    self._merge_and_normalize(nicr_group_nsf)

                nicr_nratio = Divide(nicr_group_nsf+self.suff_norm, nicr_group_sf+self.suff_norm,
                                     OutputWorkspace=nicr_group_nsf.replace('group', 'nratio'))
                nicr_nratio = Scale(nicr_nratio, OutputWorkspace=nicr_nratio.getName(), Factor=flippFac,
                                    Operation='Multiply')

                nicr_coefs_norm = Multiply(nicr_group_sf, nicr_nratio,
                                           OutputWorkspace=nicr_group_sf.replace('group', 'scaled'))

                nicr_coefs = Minus(nicr_group_nsf, nicr_coefs_norm, OutputWorkspace=out_ws_name+'_nicr_coefs_'+pol)

                nicr_coefs_normalized = Divide(nicr_coefs, nicr_coefs_norm,
                                               OutputWorkspace=out_ws_name+'_nicr_coefs_normalized_'+pol)

                AddSampleLog(nicr_coefs_normalized, LogName='ws_group', LogText=nicr_coefs_normalized.getName())

                dete_dict = {}

                for coefs_ws in nicr_coefs_normalized:
                    dete_dict[coefs_ws.getRun().getProperty('deterota').value] = coefs_ws.getName()

                nicr_coefs_dict[pol] = dete_dict

        for i in range(new_sample_table.rowCount()):

            row        = new_sample_table.row(i)
            pol_sample = row['polarisation']
            angle      = float(row['deterota'])

            if pol_sample in nicr_coefs_dict.keys():

                for key in nicr_coefs_dict[pol_sample].keys():
                    if np.fabs(angle - key) < tol:
                        angle = key

                new_sample_table.setCell('nicr_coef', i, nicr_coefs_dict[pol_sample][angle])
                new_sample_table.setCell('nicr_coef_group', i,
                                         mtd[nicr_coefs_dict[pol_sample][angle]].getRun().getProperty('ws_group').value)
            else:
                pol = nicr_coefs_dict.keys()[0]

                for key in nicr_coefs_dict[pol].keys():
                    if np.fabs(angle - key) < tol:
                        angle = key

                new_sample_table.setCell('nicr_coef', i, nicr_coefs_dict[pol][angle])
                new_sample_table.setCell('nicr_coef_group', i,
                                         mtd[nicr_coefs_dict[pol][angle]].getRun().getProperty('ws_group').value)

AlgorithmFactory.subscribe(DNSProcessNiCr)
