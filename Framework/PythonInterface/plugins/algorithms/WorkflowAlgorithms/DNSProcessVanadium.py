from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd, ITableWorkspace
from mantid.kernel import logger
from mantid.simpleapi import Plus, Divide, GroupWorkspaces, SumSpectra, Mean, DNSMergeRuns,\
    CloneWorkspace, LoadEmptyInstrument, DeleteWorkspace, Multiply, Minus

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

        self.declareProperty(name='VanadiumTable', defaultValue='', doc='Name of Table Workspace for Vanadium')
        self.declareProperty(name='BackgroundTable', defaultValue='', doc='Name of Table Workspace for Background')
        self.declareProperty(name='SampleTable', defaultValue='', doc='')
        self.declareProperty(name='OutWorkspaceName', defaultValue='')
        self.declareProperty(name='OutputXAxis', defaultValue='', doc='List of the output x axis units')
        self.declareProperty(name='Normalization', defaultValue='', doc='Type of normalization')

    def PyExec(self):

        self.vana_table = mtd[self.getProperty('VanadiumTable').value]
        self.bkg_table = mtd[self.getProperty('BackgroundTable').value]
        self.sample_table = mtd[self.getProperty('SampleTable').value]
        out_ws_name = self.getProperty('OutWorkspaceName').value

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self.instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm = self.instrument.getStringParameter('normws_suffix')[0]

        logger.debug(self.vana_table.getName())
        logger.debug(self.bkg_table.getName())
        logger.debug(self.sample_table.getName())

        self.xax = self.getProperty('OutputXAxis').value

        new_sample_table = self.sample_table.clone(OutputWorkspace= out_ws_name + '_SampleTableVanaCoef')

        new_sample_table.addColumn('str', 'vana_coef')

        if len(self.vana_table.column(0)) == len(self.sample_table.column(0)):

            vana_x_sf_ws = []
            vana_x_nsf_ws = []
            vana_y_sf_ws = []
            vana_y_nsf_ws = []
            vana_z_sf_ws = []
            vana_z_nsf_ws = []

            for i in range(len(self.vana_table.column(0))):
                row = self.vana_table.row(i)
                if row['polarisation'] == 'x':
                    if row['flipper'] == 'ON':
                        vana_x_sf_ws.append(row['run_title'])
                    else:
                        vana_x_nsf_ws.append(row['run_title'])
                elif row['polarisation'] == 'y':
                    if row['flipper'] == 'ON':
                        vana_y_sf_ws.append(row['run_title'])
                    else:
                        vana_y_nsf_ws.append(row['run_title'])
                else:
                    if row['flipper'] == 'ON':
                        vana_z_sf_ws.append(row['run_title'])
                    else:
                        vana_z_nsf_ws.append(row['run_title'])

            logger.debug('vana x sf:' + str(vana_x_sf_ws))
            logger.debug('vana x nsf:' + str(vana_x_nsf_ws))
            logger.debug('vana y sf: ' + str(vana_y_sf_ws))
            logger.debug('vana y nsf: ' + str(vana_y_nsf_ws))
            logger.debug('vana z sf: ' + str(vana_z_sf_ws))
            logger.debug('vana z nsf: ' + str(vana_z_nsf_ws))

            norm_ratio_x_sf = Divide(out_ws_name + '_rawvana_x_sf_group' + self.suff_norm,
                                     out_ws_name + '_leer_x_sf_group' + self.suff_norm,
                                     OutputWorkspace=out_ws_name+'_rawvana_x_sf_nratio')
            norm_ratio_x_nsf = Divide(out_ws_name + '_rawvana_x_nsf_group' + self.suff_norm,
                                     out_ws_name + '_leer_x_nsf_group' + self.suff_norm,
                                     OutputWorkspace=out_ws_name+'_rawvana_x_nsf_nratio')
            norm_ratio_y_sf = Divide(out_ws_name + '_rawvana_y_sf_group' + self.suff_norm,
                                     out_ws_name + '_leer_y_sf_group' + self.suff_norm,
                                     OutputWorkspace=out_ws_name+'_rawvana_y_sf_nratio')
            norm_ratio_y_nsf = Divide(out_ws_name + '_rawvana_y_nsf_group' + self.suff_norm,
                                     out_ws_name + '_leer_y_nsf_group' + self.suff_norm,
                                     OutputWorkspace=out_ws_name+'_rawvana_y_nsf_nratio')
            norm_ratio_z_sf = Divide(out_ws_name + '_rawvana_z_sf_group' + self.suff_norm,
                                     out_ws_name + '_leer_z_sf_group' + self.suff_norm,
                                     OutputWorkspace=out_ws_name+'_rawvana_z_sf_nratio')
            norm_ratio_z_nsf = Divide(out_ws_name + '_rawvana_z_nsf_group' + self.suff_norm,
                                     out_ws_name + '_leer_z_nsf_group' + self.suff_norm,
                                     OutputWorkspace=out_ws_name+'_rawvana_z_nsf_nratio')

            xsfleer_scaled = Multiply(out_ws_name+'_leer_x_sf_group', norm_ratio_x_sf,
                                      OutputWorkspace=out_ws_name+'_leer_x_sf_rawvana')
            xnsfleer_scaled = Multiply(out_ws_name+'_leer_x_nsf_group', norm_ratio_x_nsf,
                                      OutputWorkspace=out_ws_name+'_leer_x_nsf_rawvana')
            ysfleer_scaled = Multiply(out_ws_name+'_leer_y_sf_group', norm_ratio_y_sf,
                                      OutputWorkspace=out_ws_name+'_leer_y_sf_rawvana')
            ynsfleer_scaled = Multiply(out_ws_name+'_leer_y_nsf_group', norm_ratio_y_nsf,
                                      OutputWorkspace=out_ws_name+'_leer_y_nsf_rawvana')
            zsfleer_scaled = Multiply(out_ws_name+'_leer_z_sf_group', norm_ratio_z_sf,
                                      OutputWorkspace=out_ws_name+'_leer_z_sf_rawvana')
            znsfleer_scaled = Multiply(out_ws_name+'_leer_z_nsf_group', norm_ratio_z_nsf,
                                      OutputWorkspace=out_ws_name+'_leer_z_nsf_rawvana')

            Minus(out_ws_name+'_rawvana_x_sf_group', xsfleer_scaled, OutputWorkspace=out_ws_name+'_vana_x_sf_group')
            Minus(out_ws_name+'_rawvana_x_nsf_group', xnsfleer_scaled, OutputWorkspace=out_ws_name+'_vana_x_nsf_group')
            Minus(out_ws_name+'_rawvana_y_sf_group', ysfleer_scaled, OutputWorkspace=out_ws_name+'_vana_y_sf_group')
            Minus(out_ws_name+'_rawvana_y_nsf_group', ynsfleer_scaled, OutputWorkspace=out_ws_name+'_vana_y_nsf_group')
            Minus(out_ws_name+'_rawvana_z_sf_group', zsfleer_scaled, OutputWorkspace=out_ws_name+'_vana_z_sf_group')
            Minus(out_ws_name+'_rawvana_z_nsf_group', znsfleer_scaled, OutputWorkspace=out_ws_name+'_vana_z_nsf_group')

            for p in ['x', 'y', 'z']:
                self._merge_and_normalize(out_ws_name + '_vana_' + p + '_sf_group', self.xax)
                self._merge_and_normalize(out_ws_name + '_vana_' + p + '_nsf_group', self.xax)


            vana_sf_nsf_x_sum = Plus(out_ws_name + '_vana_x_sf_group',
                                     out_ws_name + '_vana_x_nsf_group')
            vana_sf_nsf_x_sum_norm = Plus(out_ws_name + 'vana_x_sf_group' + self.suff_norm,
                                          out_ws_name + '_vana_x_nsf_group' + self.suff_norm)
            print(str(vana_sf_nsf_x_sum))
            print(str(vana_sf_nsf_x_sum_norm))
            vana_total_x = SumSpectra(vana_sf_nsf_x_sum)
            vana_total_x_norm = SumSpectra(vana_sf_nsf_x_sum_norm)
            vana_mean_x = Mean(', '.join(vana_total_x.getNames()))
            vana_mean_x_norm = Mean(', '.join(vana_total_x_norm.getNames()))

            vana_coefs_x = vana_sf_nsf_x_sum/vana_mean_x
            vana_coefs_x_norm = vana_sf_nsf_x_sum_norm/vana_mean_x_norm
            vana_coefs_x_total = vana_coefs_x/vana_coefs_x_norm

            vana_coefs_dict_x = {}

            for coef_ws in vana_coefs_x_total:
                vana_coefs_dict_x[round(coef_ws.getRun().getProperty('deterota').value, 1)] = coef_ws.getName()

            vana_sf_nsf_y_sum = Plus(out_ws_name + '_vana_y_sf_group', out_ws_name + '_vana_y_nsf_group')
            vana_sf_nsf_y_sum_norm = Plus(out_ws_name + '_vana_y_sf_group' + self.suff_norm,
                                          out_ws_name + '_vana_y_nsf_group' + self.suff_norm)
            print(str(vana_sf_nsf_y_sum))
            print(str(vana_sf_nsf_y_sum_norm))
            vana_total_y = SumSpectra(vana_sf_nsf_y_sum)
            vana_total_y_norm = SumSpectra(vana_sf_nsf_y_sum_norm)
            vana_mean_y = Mean(', '.join(vana_total_y.getNames()))
            vana_mean_y_norm = Mean(', '.join(vana_total_y_norm.getNames()))
            vana_coefs_y = vana_sf_nsf_y_sum/vana_mean_y
            vana_coefs_y_norm = vana_sf_nsf_y_sum_norm/vana_mean_y_norm
            vana_coefs_y_total = vana_coefs_y/vana_coefs_y_norm

            vana_coefs_dict_y = {}

            for coef_ws in vana_coefs_y_total:
                vana_coefs_dict_y[round(coef_ws.getRun().getProperty('deterota').value, 1)] = coef_ws.getName()

            vana_sf_nsf_z_sum = Plus(out_ws_name + '_vana_z_sf_group', out_ws_name + '_vana_z_nsf_group')
            vana_sf_nsf_z_sum_norm = Plus(out_ws_name + '_vana_z_sf_group' + self.suff_norm,
                                          out_ws_name + '_vana_z_nsf_group' + self.suff_norm)
            print(str(vana_sf_nsf_z_sum))
            print(str(vana_sf_nsf_z_sum_norm))
            vana_total_z = SumSpectra(vana_sf_nsf_z_sum)
            vana_total_z_norm = SumSpectra(vana_sf_nsf_z_sum_norm)
            vana_mean_z = Mean(', '.join(vana_total_z.getNames()))
            vana_mean_z_norm = Mean(', '.join(vana_total_z_norm.getNames()))
            vana_coefs_z = vana_sf_nsf_z_sum/vana_mean_z
            vana_coefs_z_norm = vana_sf_nsf_z_sum_norm/vana_mean_z_norm
            vana_coefs_z_total = vana_coefs_z/vana_coefs_z_norm

            vana_coefs_dict_z = {}

            for coef_ws in vana_coefs_z_total:
                vana_coefs_dict_z[round(coef_ws.getRun().getProperty('deterota').value, 1)] = coef_ws.getName()

            for i in range(len(new_sample_table.column(0))):
                row = new_sample_table.row(i)
                if row['polarization'] == 'x':
                    new_sample_table.setCell('vana_coef', i, vana_coefs_dict_x[round(float(row['deterota']), 1)])
                if row['polarization'] == 'y':
                    new_sample_table.setCell('vana_coef', i, vana_coefs_dict_y[round(float(row['deterota']), 1)])
                if row['polarization'] == 'z':
                    new_sample_table.setCell('vana_coef', i, vana_coefs_dict_z[round(float(row['deterota']), 1)])

        elif len(self.sample_table.column(0))/3 == len(self.vana_table.column(0)):

            vana_sf_ws = []
            vana_nsf_ws = []
            pol = None

            for i in range(len(self.vana_table.column(0))):
                row = self.vana_table.row(i)
                if row['flipper'] == 'ON':
                    vana_sf_ws.append(row['run_title'])
                    pol = row['polarisation']
                else:
                    vana_nsf_ws.append(row['run_title'])

            norm_ratio_sf = Divide(out_ws_name + '_rawvana_' + pol + '_sf_group' + self.suff_norm,
                                   out_ws_name + '_leer_' + pol + '_sf_group' + self.suff_norm,
                                   OutputWorkspace=out_ws_name + '_rawvana_' + pol + '_sf_nratio')
            norm_ratio_nsf = Divide(out_ws_name + '_rawvana_' + pol + '_nsf_group' + self.suff_norm,
                                   out_ws_name + '_leer_' + pol + '_nsf_group' + self.suff_norm,
                                   OutputWorkspace=out_ws_name + '_rawvana_' + pol + '_nsf_nratio')

            sfleer_scaled = Multiply(out_ws_name + '_leer_' + pol + '_sf_group', norm_ratio_sf,
                                     OutputWorkspace=out_ws_name +'_leer_' + pol + "_sf_rawvana")
            nsfleer_scaled = Multiply(out_ws_name + '_leer_' + pol + '_nsf_group', norm_ratio_nsf,
                                      OutputWorkspace=out_ws_name +'_leer_' + pol + "_nsf_rawvana")

            Minus(out_ws_name + '_rawvana_' + pol + '_sf_group', sfleer_scaled,
                  OutputWorkspace=out_ws_name+'_vana_'+pol+'_sf_group')
            CloneWorkspace(out_ws_name + '_rawvana_' + pol + '_sf_group' + self.suff_norm,
                           OutputWorkspace=out_ws_name+'_vana_'+pol+'_sf_group' + self.suff_norm)
            Minus(out_ws_name + '_rawvana_' + pol + '_nsf_group', nsfleer_scaled,
                  OutputWorkspace=out_ws_name+'_vana_'+pol+'_nsf_group')
            CloneWorkspace(out_ws_name + '_rawvana_' + pol + '_nsf_group' + self.suff_norm,
                           OutputWorkspace=out_ws_name+'_vana_'+pol+'_nsf_group' + self.suff_norm)
            self._merge_and_normalize(out_ws_name + '_vana_' + pol + '_sf_group', self.xax)
            self._merge_and_normalize(out_ws_name + '_vana_' + pol + '_nsf_group', self.xax)

            vana_sf_nsf_sum = Plus(out_ws_name + '_vana_' + pol + "_sf_group",
                                   out_ws_name + '_vana_' + pol + "_nsf_group")
            vana_sf_nsf_sum_norm = Plus(out_ws_name + '_vana_' + pol + "_sf_group" + self.suff_norm,
                                        out_ws_name + '_vana_' + pol + "_nsf_group" + self.suff_norm)

            vana_total = SumSpectra(vana_sf_nsf_sum)
            vana_total_norm = SumSpectra(vana_sf_nsf_sum_norm)
            vana_mean = Mean(', '.join(vana_total.getNames()))
            vana_mean_norm = Mean(', '.join(vana_total_norm.getNames()))
            vana_coefs = vana_sf_nsf_sum/vana_mean
            vana_coefs_norm = vana_sf_nsf_sum_norm/vana_mean_norm
            vana_coefs_total = vana_coefs/vana_coefs_norm
            vana_coefs_dict = {}

            #for coef_ws in vana_coefs:
            for coef_ws in vana_coefs_total:
                logger.debug(str(round(coef_ws.getRun().getProperty('deterota').value, 1)))
                vana_coefs_dict[round(coef_ws.getRun().getProperty('deterota').value, 1)] = coef_ws.getName()

            for i in range(len(new_sample_table.column(0))):
                row = new_sample_table.row(i)
                new_sample_table.setCell('vana_coef', i, vana_coefs_dict[round(float(row['deterota']), 1)])
                print(str(row))




AlgorithmFactory.subscribe(DNSProcessVanadium)