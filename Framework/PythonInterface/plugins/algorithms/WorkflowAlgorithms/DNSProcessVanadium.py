from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd, ITableWorkspace
from mantid.kernel import logger
from mantid.simpleapi import Plus, Divide, GroupWorkspaces, SumSpectra, Mean, DNSMergeRuns, CloneWorkspace

import numpy as np

class DNSProcessVanadium(PythonAlgorithm):

    def _merge_and_normalize(self, wsgroup, xax, namex= ''):
        for x in xax:
            data_merged = DNSMergeRuns(wsgroup + namex, x, OutputWorkspace=wsgroup + '_m0' + '_' + x)
            norm_merged = DNSMergeRuns(wsgroup + '_norm' + namex, x, OutputWorkspace=wsgroup + '_norm_m' + '_' + x)
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

        logger.debug(self.vana_table.getName())
        logger.debug(self.bkg_table.getName())
        logger.debug(self.sample_table.getName())

        new_sample_table = self.sample_table.clone(OutputWorkspace= out_ws_name + '_SampleTableVanaCoef')

        new_sample_table.addColumn('str', 'vana')
        new_sample_table.addColumn('str', 'coef')

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

        vana_sf_nsf_x_sum = None
        vana_sf_nsf_y_sum = None
        vana_sf_nsf_z_sum = None

        if vana_x_sf_ws and vana_x_nsf_ws:
            vana_sf_nsf_x_sum = Plus(out_ws_name + '_rawvana_x_sf_group', out_ws_name + '_rawvana_x_nsf_group')
        if vana_y_sf_ws and vana_y_nsf_ws:
            vana_sf_nsf_y_sum = Plus(out_ws_name + '_rawvana_y_sf_group', out_ws_name + '_rawvana_y_nsf_group')
        if vana_z_sf_ws and vana_z_nsf_ws:
            vana_sf_nsf_z_sum = Plus(out_ws_name + '_rawvana_z_sf_group', out_ws_name + '_rawvana_z_nsf_group')

        vana_total_x = None
        vana_total_y = None
        vana_total_z = None
        vana_mean_x = None
        vana_mean_y = None
        vana_mean_z = None

        if vana_sf_nsf_x_sum:
            print(str(vana_sf_nsf_x_sum))
            vana_total_x = SumSpectra(vana_sf_nsf_x_sum)
            vana_mean_x = Mean(', '.join(vana_total_x.getNames()))
            vana_coefs_x = vana_sf_nsf_x_sum/vana_mean_x
        if vana_sf_nsf_y_sum:
            print(str(vana_sf_nsf_y_sum))
            vana_total_y = SumSpectra(vana_sf_nsf_y_sum)
            vana_mean_y = Mean(', '.join(vana_total_y.getNames()))
            vana_coefs_y = vana_sf_nsf_y_sum/vana_mean_y
        if vana_sf_nsf_z_sum:
            print(str(vana_sf_nsf_z_sum))
            vana_total_z = SumSpectra(vana_sf_nsf_z_sum)
            vana_mean_z = Mean(', '.join(vana_total_z.getNames()))
            vana_coefs_z = vana_sf_nsf_z_sum/vana_mean_z





        for i in range(len(new_sample_table.column(0))):
            row = new_sample_table.row(i)
            print(str(row))


AlgorithmFactory.subscribe(DNSProcessVanadium)