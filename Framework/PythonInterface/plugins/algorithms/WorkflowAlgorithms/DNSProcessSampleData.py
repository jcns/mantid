from __future__ import (absolute_import, division, print_function)

from mantid.api import PyhonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import logger
from mantid.simpleapi import Divide, Multiply, Minus, CloneWorkspace


class DNSProcessSampleData(PyhonAlgorithm):

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty('SampleTable', defaultValue='')
        self.declareProperty('SubtractBackground', defaultValue='')
        self.declareProperty('DeteEffiCorrection', defaultValue='')
        self.declareProperty('FlippRatioCorrection', defaultValue='')
        self.declareProperty('OutputWorkspaceName', defaultValue='')

    def PyExec(self):

        sample_table = mtd[self.getProperty('SampleTable').value]
        subInst = self.getProperty('SubtractBackground').value
        detEffi = self.getProptery('DeteEffiCorrection').value
        flippRatio = self.getPropery('FlippingRatioCorrection').value
        out_ws_name = self.getProperty('OutputWorkspaceName').value

        logger.debug(sample_table.getName())
        logger.debug(subInst)
        logger.debug(detEffi)
        logger.debug(flippRatio)
        logger.debug(out_ws_name)

        if subInst:
            for p in ['_x', '_y', '_z']:
                for flip in ['_sf', '_nsf']:
                    inws = out_ws_name + '_rawdata' + p + flip + '_group'
                    bkgws = out_ws_name + '_leer' + p + flip + '_group'
                    if mtd.doesExist(inws):
                        #print('Sub bkg. data: ', inws, ' bkg: ', bkgws)
                        #norm_ratio[p + flip] = Divide(inws + self.suff_norm, bkgws + self.suff_norm,
                        #                              OutputWorkspace=out_ws_name + '_rawdata' + p + flip + '_nratio')
                        #leer_scaled[p + flip] = Multiply(bkgws, norm_ratio[p + flip],
                        #                                 OutputWorkspace=out_ws_name + '_leer' + p + flip + '_rawdata')
                        #Minus(inws, leer_scaled[p + flip], OutputWorkspace=out_ws_name + '_data' + p + flip + '_group')
                        #CloneWorkspace(inws + self.suff_norm,
                        #               OutputWorkspace=out_ws_name + '_data' + p + flip + '_group' + self.suff_norm)
                        #self._merge_and_normalize(out_ws_name + '_data' + p + flip + '_group', self.xax)
                        #bkgws = ws_name+'_leer'+p+flip+'_group'
                        resws = out_ws_name+'_data'+p+flip+'_group'
                        Minus(inws,bkgws,OutputWorkspace=resws)
        else:
            for p in ['_x', '_y', '_z']:
                for flip in ['_sf', '_nsf']:
                    inws = out_ws_name + '_rawdata' + p + flip + '_group'
                    if mtd.doesExist(inws):
                        CloneWorkspace(inws, out_ws_name + '_data' + p + flip + '_group')

AlgorithmFactory.subscribe(DNSProcessSampleData)
