from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import logger
from mantid.simpleapi import Divide, Multiply, Minus, CloneWorkspace, Plus, GroupWorkspaces


class DNSProcessSampleData(PythonAlgorithm):

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
        detEffi = self.getProperty('DeteEffiCorrection').value
        flippRatio = self.getProperty('FlippRatioCorrection').value
        out_ws_name = self.getProperty('OutputWorkspaceName').value

        logger.debug(sample_table.getName())
        logger.debug(subInst)
        logger.debug(detEffi)
        logger.debug(flippRatio)
        logger.debug(out_ws_name)

        if subInst == "True":
            for i in range(len(sample_table.column(0))):
                data_ws = sample_table.cell('run_title', i)
                bkg_ws = sample_table.cell('Background ws', i)
                Minus(data_ws, bkg_ws, OutputWorkspace=data_ws+"_sub_bkg")
                sample_table.setCell('run_title', i, data_ws+"_sub_bkg")
            #for p in ['_x', '_y', '_z']:
                #for flip in ['_sf', '_nsf']:
                    #inws = out_ws_name + '_rawdata' + p + flip + '_group'
                    #kgws = out_ws_name + '_leer' + p + flip + '_group'
                    #if mtd.doesExist(inws):
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
                        #resws = out_ws_name+'_data'+p+flip+'_group'
                        #Minus(inws,bkgws,OutputWorkspace=resws)
        #else:
            #for p in ['_x', '_y', '_z']:
            #    for flip in ['_sf', '_nsf']:
            #        inws = out_ws_name + '_rawdata' + p + flip + '_group'
            #        if mtd.doesExist(inws):
            #            CloneWorkspace(inws, out_ws_name + '_data' + p + flip + '_group')

        if detEffi == "True":
            for i in range(len(sample_table.column(0))):
                data_ws = sample_table.cell('run_title', i)
                vana_coef = sample_table.cell('vana_coef', i)
                print(str(data_ws) + ", " + str(vana_coef))
                Divide(data_ws, vana_coef, OutputWorkspace=data_ws+'_vana_corr')
                sample_table.setCell('run_title', i, data_ws+'_vana_corr')


        j = 1
        while sample_table.cell('deterota', j) != sample_table.cell("deterota", 0):
            j = j +1
        offset = j
        print(str(offset))
        group_sf = []
        group_nsf = []
        if flippRatio == "True":
            print(bool(flippRatio))
            for i in range(len(sample_table.column(0))):
                print(str(i))
                data_ws= sample_table.cell('run_title', i)
                nicr_coef = sample_table.cell('Nicr ws', i)
                coef = 1/mtd[nicr_coef]
                print(str(coef))
                print("flip: " + sample_table.cell('flipper', i) )
                if sample_table.cell('flipper', i) == 'OFF':
                    print("OFF")
                    Minus(data_ws, sample_table.cell('run_title', i-offset), OutputWorkspace=data_ws+"_nicr_corr")
                    Multiply(data_ws+'_nicr_corr', coef, OutputWorkspace=data_ws+'_nicr_corr')
                    Plus(data_ws, data_ws+'_nicr_corr', OutputWorkspace=data_ws+'_nicr_corr')
                    group_nsf.append(sample_table.cell('run_title', i))
                else:
                    Minus(data_ws, sample_table.cell('run_title', i+offset), OutputWorkspace=data_ws+"_nicr_corr")
                    Multiply(data_ws+'_nicr_corr', coef, OutputWorkspace=data_ws+'_nicr_corr')
                    Minus(data_ws, data_ws+'_nicr_corr', OutputWorkspace=data_ws+'_nicr_corr')
                    group_sf.append(sample_table.cell('run_title', i))
                sample_table.setCell('run_title', i, data_ws+'_nicr_corr')
        else:
            for i in range(len(sample_table.column(0))):
                if sample_table.cell('flipper', i) == "OFF":
                    group_nsf.append(sample_table.cell('run_title', i))
                else:
                    group_sf.append(sample_table.cell('run_title', i))

        GroupWorkspaces(group_nsf, OutputWorkspace=out_ws_name+'_nsf')
        GroupWorkspaces(group_sf, OutputWorkspace=out_ws_name+'_sf')


        print(str(offset))


AlgorithmFactory.subscribe(DNSProcessSampleData)
