from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd, ITableWorkspace
from mantid.kernel import logger

class DNSProcessVanadium(PythonAlgorithm):

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name='VanadiumTable', defaultValue='', doc='Name of Table Workspace for Vanadium')
        self.declareProperty(name='BackgroundTable', defaultValue='', doc='Name of Table Workspace for Background')
        self.declareProperty(name='SampleTable', defaultValue='', doc='')
        self.declareProperty(name='OutWorkspaceName', defaultValue='')

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
                    vana_x_sf_ws.append(mtd[row['run_title']])
                else:
                    vana_x_nsf_ws.append(mtd[row['run_title']])
            elif row['polarisation'] == 'y':
                if row['flipper'] == 'ON':
                    vana_y_sf_ws.append(mtd[row['run_title']])
                else:
                    vana_y_nsf_ws.append([mtd[row['run_title']]])
            else:
                if row['flipper'] == 'ON':
                    vana_z_sf_ws.append(mtd[row['run_title']])
                else:
                    vana_z_nsf_ws.append(mtd[row['run_title']])

        logger.debug('vana x sf:' + str(vana_x_sf_ws))
        logger.debug('vana x nsf:' + str(vana_x_nsf_ws))
        logger.debug('vana y sf: ' + str(vana_y_sf_ws))
        logger.debug('vana y nsf: ' + str(vana_y_nsf_ws))
        logger.debug('vana z sf: ' + str(vana_z_sf_ws))
        logger.debug('vana z nsf: ' + str(vana_z_nsf_ws))


        for i in range(len(new_sample_table.column(0))):
            row = new_sample_table.row(i)
            print(str(row))


AlgorithmFactory.subscribe(DNSProcessVanadium)