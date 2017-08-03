from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.simpleapi import Plus, Divide, SumSpectra, Mean, DNSMergeRuns, \
    CloneWorkspace, LoadEmptyInstrument, DeleteWorkspace, Multiply, Minus, AddSampleLog

import numpy as np


class DNSProcessVanadium(PythonAlgorithm):

    def _merge_and_normalize(self, wsgroup):
        x_axis = self.xax.split(', ')
        for x in x_axis:
            data_merged = DNSMergeRuns(wsgroup, x, OutputWorkspace=wsgroup+'_m0'+'_'+x)
            norm_merged = DNSMergeRuns(wsgroup+self.suff_norm, x, OutputWorkspace=wsgroup+self.suff_norm+'_m'+'_'+x)

            try:
                Divide(data_merged, norm_merged, OutputWorkspace=wsgroup+'_m'+'_'+x)
            except:
                data_x = data_merged.extractX()
                norm_merged.setX(0, data_x[0])
                Divide(data_merged, norm_merged, OutputWorkspace=wsgroup+'_m'+'_'+x)

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name='SampleTable',     defaultValue='', doc='Name of the sample data ITableWorkspace')
        self.declareProperty(name='VanadiumTable',   defaultValue='', doc='Name of the vanadium ITableWorkspace')
        self.declareProperty(name='OutputWorkspace', defaultValue='', doc='Name for the output Workspace')
        self.declareProperty(name='OutputXAxis',     defaultValue='', doc='List of the output x axis units')
        self.declareProperty(name='Polarisations',   defaultValue='', doc='')
        self.declareProperty(name='SingleCrystal',   defaultValue='', doc='')

    def PyExec(self):

        sample_table = mtd[self.getProperty('SampleTable').value]
        vana_table   = mtd[self.getProperty('VanadiumTable').value]

        out_ws_name      = self.getProperty('OutputWorkspace').value
        new_sample_table = sample_table.clone(OutputWorkspace=out_ws_name+'_SampleTableVanaCoef')

        self.xax           = self.getProperty('OutputXAxis').value
        polarisations = self.getProperty('Polarisations').value.split(', ')

        sc      = self.getProperty('SingleCrystal').value
        self.sc = eval(sc)

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm = instrument.getStringParameter('normws_suffix')[0]
        tol            = float(instrument.getStringParameter('two_theta_tolerance')[0])
        self._m_and_n  = instrument.getBoolParameter("keep_intermediate_workspace")[0]

        offset = 0

        gr  = vana_table.cell('ws_group', 0)
        gr2 = vana_table.cell('ws_group', offset)
        while gr == gr2:
            offset += 1
            gr2 = vana_table.cell('ws_group', offset)

        new_sample_table.addColumn('str', 'vana_coef')
        new_sample_table.addColumn('str', 'vana_coef_group')

        row = 0
        vana_coefs_dict = {}

        while row < vana_table.rowCount():

            pol = vana_table.cell('polarisation', row)

            vana_group_sf = vana_table.cell('ws_group', row)
            bkg_group_sf  = vana_group_sf.replace("rawvana", "leer", 1)

            row = row + offset

            vana_group_nsf = vana_table.cell('ws_group', row)
            bkg_group_nsf  = vana_group_nsf.replace("rawvana", "leer", 1)

            row = row + offset

            if pol in polarisations:

                norm_ratio_sf  = Divide(vana_group_sf+self.suff_norm, bkg_group_sf+self.suff_norm,
                                        OutputWorkspace=vana_group_sf+'_nratio')
                norm_ratio_nsf = Divide(vana_group_nsf+self.suff_norm, bkg_group_nsf+self.suff_norm,
                                        OutputWorkspace=vana_group_nsf+'_nratio')

                leer_scaled_sf  = Multiply(bkg_group_sf, norm_ratio_sf,
                                           OutputWorkspace=bkg_group_sf.replace('group', 'vana'))
                leer_scaled_nsf = Multiply(bkg_group_nsf, norm_ratio_nsf,
                                           OutputWorkspace=bkg_group_nsf.replace('group', 'vana'))

                Minus(vana_group_sf, leer_scaled_sf, OutputWorkspace=vana_group_sf.replace('raw', ''))
                CloneWorkspace(vana_group_sf+self.suff_norm,
                               OutputWorkspace=vana_group_sf.replace('raw', '')+self.suff_norm)

                Minus(vana_group_nsf, leer_scaled_nsf, OutputWorkspace=vana_group_nsf.replace('raw', ''))
                CloneWorkspace(vana_group_nsf+self.suff_norm,
                               OutputWorkspace=vana_group_nsf.replace('raw', '')+self.suff_norm)

                vana_group_sf  = vana_group_sf.replace('raw', '')
                vana_group_nsf = vana_group_nsf.replace('raw', '')

                if self._m_and_n and not self.sc:
                    self._merge_and_normalize(vana_group_sf)
                    self._merge_and_normalize(vana_group_nsf)

                vana_sf_nsf_sum      = Plus(vana_group_sf, vana_group_nsf,
                                            OutputWorkspace=out_ws_name+'_vana_sf_nsf_sum_'+pol)
                vana_sf_nsf_sum_norm = Plus(vana_group_sf+self.suff_norm, vana_group_nsf+self.suff_norm,
                                            OutputWorkspace=out_ws_name+'_vana_sf_nsf_sum_norm_'+pol)

                vana_total      = SumSpectra(vana_sf_nsf_sum,      OutputWorkspace=out_ws_name+'_vana_total_'+pol)
                vana_total_norm = SumSpectra(vana_sf_nsf_sum_norm, OutputWorkspace=out_ws_name+'_vana_total_norm_'+pol)

                vana_mean      = Mean(', '.join(vana_total.getNames()), OutputWorkspace=out_ws_name+'_vana_mean_'+pol)
                vana_mean_norm = Mean(', '.join(vana_total_norm.getNames()),
                                      OutputWorkspace=out_ws_name+'_vana_mean_norm_'+pol)

                vana_coefs      = Divide(vana_sf_nsf_sum, vana_mean, OutputWorkspace=out_ws_name+'_vana_coefs_'+pol)
                vana_coefs_norm = Divide(vana_sf_nsf_sum_norm, vana_mean_norm,
                                         OutputWorkspace=out_ws_name+'_vana_coefs_norm_'+pol)

                vana_coefs_total = Divide(vana_coefs, vana_coefs_norm,
                                          OutputWorkspace=out_ws_name+'_vana_coefs_total_'+pol)

                AddSampleLog(vana_coefs_total, LogName='ws_group', LogText=vana_coefs_total.getName())

                deterota = []
                dete_dict = {}

                for coef_ws in vana_coefs_total:
                    deterota.append(coef_ws.getRun().getProperty('deterota').value)
                    dete_dict[coef_ws.getRun().getProperty('deterota').value] = coef_ws.getName()

                vana_coefs_dict[pol] = dete_dict

        for i in range(new_sample_table.rowCount()):

            row = new_sample_table.row(i)

            pol_sample = row['polarisation']
            angle      = float(row['deterota'])

            if pol_sample in vana_coefs_dict.keys():

                for key in vana_coefs_dict[pol_sample].keys():
                    if np.fabs(angle - key) < tol:
                        angle = key

                new_sample_table.setCell('vana_coef', i, vana_coefs_dict[pol_sample][angle])
                new_sample_table.setCell('vana_coef_group', i,
                                         mtd[vana_coefs_dict[pol_sample][angle]].getRun().getProperty('ws_group').value)
            else:

                pol = vana_coefs_dict.keys()[0]
                for key in vana_coefs_dict[pol].keys():
                    if np.fabs(angle - key) < tol:
                        angle = key

                new_sample_table.setCell('vana_coef', i, vana_coefs_dict[pol][angle])
                new_sample_table.setCell('vana_coef_group', i,
                                         mtd[vana_coefs_dict[pol][angle]].getRun().getProperty('ws_group').value)

AlgorithmFactory.subscribe(DNSProcessVanadium)
