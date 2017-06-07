from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, ITableWorkspace, mtd
from mantid.kernel import logger
from mantid.simpleapi import LoadEmptyInstrument,GroupWorkspaces, DeleteWorkspace, Divide, Multiply, Minus, \
    CloneWorkspace, DNSMergeRuns

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
        self.declareProperty(name='NiCrTable', defaultValue='')
        self.declareProperty(name='SampleTable', defaultValue='')
        self.declareProperty(name='OutputWorkspaceName', defaultValue='')
        self.declareProperty(name='XAxisUnits', defaultValue='')
        self.declareProperty(name='DetEffiCorrection', defaultValue='')
        self.declareProperty(name='FlippCorrFactor', defaultValue='')

    def PyExec(self):

        self.nicr_table = mtd[self.getProperty('NiCrTable').value]
        self.sample_table = mtd[self.getProperty('SampleTable').value]
        self.out_ws_name = self.getProperty('OutputWorkspaceName').value
        self.xax = self.getProperty('XAxisUnits').value
        self.detEffi = self.getProperty('DetEffiCorrection').value
        self.flippFac = self.getProperty('FlippCorrFactor').value

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self.instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm = self.instrument.getStringParameter('normws_suffix')[0]

        logger.debug(self.nicr_table.getName())
        logger.debug(self.sample_table.getName())

        new_sample_table = self.sample_table.clone(OutputWorkspace=self.out_ws_name+'_SampleTableNiCrCoef')
        new_sample_table.addColumn('str', 'nicr_coef')

        """for p in ['_x', '_y', '_z']:
            for flipp in ['_sf', '_nsf']:
                wname = self.out_ws_name+'_rawnicr'+p+flipp+'_group'
                norm_ratio = Divide(wname+self.suff_norm, self.out_ws_name+'_leer'+p+flipp+'_group'+self.suff_norm,
                                    OutputWorkspace=self.out_ws_name+'_rawnicr'+p+flipp+'_nratio')
                leer_scaled = Multiply(self.out_ws_name+'_leer'+p+flipp+'_group', norm_ratio,
                                       OutputWorkspace=self.out_ws_name+'_leer'+p+flipp+'_rawnicr')
                Minus(wname, leer_scaled, OutputWorkspace=self.out_ws_name+'_nicr'+p+flipp+'_group')
                CloneWorkspace(wname+self.suff_norm,
                               OutputWorkspace=self.out_ws_name+'_nicr'+p+flipp+'_group'+self.suff_norm)
                self._merge_and_normalize(self.out_ws_name+'_nicr'+p+flipp+'_group', self.xax)

        coefs_norm = {}

        nicr_ratio_x = Divide(self.out_ws_name+'_nicr_x_nsf'+'_group'+self.suff_norm,
                            self.out_ws_name+'_nicr_x_sf'+'_group'+self.suff_norm,
                            OutputWorkspace=self.out_ws_name+'_nicr_x_nsf_scaled')
        nicr_coefs_norm_x = Multiply(self.out_ws_name+'_nicr_x_sf_group', nicr_ratio_x,
                                   OutputWorkspace=self.out_ws_name+'_nicr_x_sf_scaled')
        nicr_coefs_x = Minus(self.out_ws_name+'_nicr_x_nsf_group', nicr_coefs_norm_x)
        nicr_coefs_normalized_x = nicr_coefs_x/nicr_coefs_norm_x
        coefs_norm['x'] = nicr_coefs_normalized_x

        nicr_ratio_y = Divide(self.out_ws_name+'_nicr_y_nsf'+'_group'+self.suff_norm,
                            self.out_ws_name+'_nicr_y_sf'+'_group'+self.suff_norm,
                            OutputWorkspace=self.out_ws_name+'_nicr_y_nsf_scaled')
        nicr_coefs_norm_y = Multiply(self.out_ws_name+'_nicr_y_sf_group', nicr_ratio_y,
                                   OutputWorkspace=self.out_ws_name+'_nicr_y_sf_scaled')
        nicr_coefs_y = Minus(self.out_ws_name+'_nicr_y_nsf_group', nicr_coefs_norm_y)
        nicr_coefs_normalized_y = nicr_coefs_y/nicr_coefs_norm_y
        coefs_norm['y'] = nicr_coefs_normalized_y

        nicr_ratio_z = Divide(self.out_ws_name+'_nicr_z_nsf'+'_group'+self.suff_norm,
                            self.out_ws_name+'_nicr_z_sf'+'_group'+self.suff_norm,
                            OutputWorkspace=self.out_ws_name+'_nicr_z_nsf_scaled')
        nicr_coefs_norm_z = Multiply(self.out_ws_name+'_nicr_z_sf_group', nicr_ratio_z,
                                   OutputWorkspace=self.out_ws_name+'_nicr_z_sf_scaled')
        nicr_coefs_z = Minus(self.out_ws_name+'_nicr_z_nsf_group', nicr_coefs_norm_z)
        nicr_coefs_normalized_z = nicr_coefs_z/nicr_coefs_norm_z
        coefs_norm['z'] = nicr_coefs_normalized_z"""

        coefs_norm = {}

        for p in ['_x', '_y', '_z']:
            for flipp in ['_sf', '_nsf']:
                nicr_ws = self.out_ws_name+'_rawnicr'+p+flipp+'_group'
                bkg_ws = self.out_ws_name+'_leer'+p+flipp+'_group'
                Minus(nicr_ws, bkg_ws, OutputWorkspace=self.out_ws_name+'_nicr'+p+flipp+'_group')

        for p in ['_x', '_y', '_z']:
            nicr_coef = Divide(self.out_ws_name+'_nicr'+p+'_nsf_group', self.out_ws_name+'_nicr'+p+'_sf_group',
                               OutputWorkspace=self.out_ws_name+'_nicr_coef'+p)
            for ws in mtd[self.out_ws_name+'_nicr_coef'+p]:
                print(ws)
                ws = ws * self.flippFac - 1.0

            coefs_norm[p[1:]] = nicr_coef

        for coef in coefs_norm:
            deterota_dict = {}
            for ws in coefs_norm[coef]:
                deterota_dict[round(ws.getRun().getProperty('deterota').value-0.5)] = ws.getName()
            coefs_norm[coef] = deterota_dict

        print(str(coefs_norm))

        for i in range(len(new_sample_table)):
            row = new_sample_table.row(i)
            new_sample_table.setCell('nicr_coef', i,
                                     coefs_norm[row['polarisation']][round(float(row['deterota'])-0.05)])

AlgorithmFactory.subscribe(DNSProcessNiCr)
