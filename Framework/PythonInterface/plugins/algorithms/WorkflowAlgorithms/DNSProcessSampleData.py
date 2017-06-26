from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import logger
from mantid.simpleapi import Divide, Multiply, Minus, CloneWorkspace, Plus, \
    LoadEmptyInstrument, DeleteWorkspace, DNSMergeRuns, Scale

import numpy as np

import os


class DNSProcessSampleData(PythonAlgorithm):

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

    def _save_to_file(self, fsuffix, axis_suffix, flipp='', pol=''):
        axis_dict = {'|Q|': 'Q[A-1]', 'd-Spacing': 'd[A]', '2theta': 'theta[degree]'}
        xarrays = []
        xs = 0
        header = ''
        ws1 = mtd[self.out_ws_name+fsuffix+axis_suffix.split(', ')[0]]
        for x in axis_suffix.split(', '):
            ws = mtd[self.out_ws_name+fsuffix+x]
            print(x)
            xarrays.append(np.array(ws.extractX()[0]))
            if x != '2theta':
                header += axis_dict[x] + '\t\t'
            else:
                header += axis_dict[x] +'\t'

        y = np.array(ws1.extractY()[0])
        err = np.array(ws1.extractE()[0])
        header += 'I\t\tError'
        fname = os.path.join(self.out_file_directory, self.out_file_prefix+pol+flipp+'.txt')
        xarrays.append(y)
        xarrays.append(err)
        np.savetxt(fname, np.transpose(xarrays), fmt='%1.4e', delimiter='\t', header=header, newline=os.linesep)

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty('SampleTable', defaultValue='', doc='Name of the sample data ITable Workspace')
        self.declareProperty('SubtractBackground', defaultValue='', doc='Bool if subtract background for sample')
        self.declareProperty('DeteEffiCorrection', defaultValue='', doc='Bool if correct detector efficiency')
        self.declareProperty('FlippRatioCorrection', defaultValue='', doc='Bool if correct flipping ratio')
        self.declareProperty('OutputFileDirectory', defaultValue='', doc='Directory to save files')
        self.declareProperty('OutputFilePrefix', defaultValue='', doc='Prefix of the files to save')
        self.declareProperty('OutputWorkspace', defaultValue='', doc='Name of the output workspace')
        self.declareProperty('OutputXAxis', defaultValue='', doc='List of the output x axis units')
        self.declareProperty('SampleParameters', defaultValue='', doc='Dictionary of the parameters for the sample')


    def PyExec(self):

        sample_table = mtd[self.getProperty('SampleTable').value]
        subInst = self.getProperty('SubtractBackground').value
        detEffi = self.getProperty('DeteEffiCorrection').value
        flippRatio = self.getProperty('FlippRatioCorrection').value
        self.out_file_prefix = self.getProperty('OutputFilePrefix').value
        self.out_file_directory = self.getProperty('OutputFileDirectory').value
        self.out_ws_name = self.getProperty('OutputWorkspace').value
        self.xax = self.getProperty('OutputXAxis').value
        parameters = self.getProperty('SampleParameters').value
        self.sampleParameters = eval(parameters)

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self.instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm = self.instrument.getStringParameter('normws_suffix')[0]

        logger.debug(sample_table.getName())
        logger.debug(subInst)
        logger.debug(detEffi)
        logger.debug(flippRatio)
        logger.debug(self.out_ws_name)

        offset = 0
        gr1 = sample_table.cell('ws_group', 0)
        gr2 = sample_table.cell('ws_group', offset)
        while gr1 == gr2:
            offset += 1
            gr2 = sample_table.cell('ws_group', offset)

        logger.debug('rows: ' + str(sample_table.rowCount()))

        if subInst == "True":
            row = 0
            while row < sample_table.rowCount():

                data_group_sf = sample_table.cell('ws_group', row)
                bkg_group_sf = sample_table.cell('background_group_ws', row)

                print('data group: ', data_group_sf, ", bkg group: ", bkg_group_sf)

                row += offset

                data_group_nsf = sample_table.cell('ws_group', row)
                bkg_group_nsf = sample_table.cell('background_group_ws', row)

                print('data group: ', data_group_nsf, ", bkg group: ", bkg_group_nsf)

                row += offset

                norm_ratio_sf = Divide(data_group_sf+self.suff_norm, bkg_group_sf+self.suff_norm,
                                       OutputWorkspace=data_group_sf+'_nratio')
                norm_ratio_nsf = Divide(data_group_nsf+self.suff_norm, bkg_group_nsf+self.suff_norm,
                                        OutputWorkspace=data_group_nsf+'_nratio')

                leer_scaled_sf = Multiply(bkg_group_sf, norm_ratio_sf,
                                          OutputWorkspace=bkg_group_sf.replace('group', 'rawdata'))
                leer_scaled_nsf = Multiply(bkg_group_nsf, norm_ratio_nsf,
                                           OutputWorkspace=bkg_group_nsf.replace('group', 'rawdata'))

                Minus(data_group_sf, leer_scaled_sf, OutputWorkspace=data_group_sf.replace('raw', ''))
                CloneWorkspace(data_group_sf+self.suff_norm,
                               OutputWorkspace=data_group_sf.replace('raw', '')+self.suff_norm)

                Minus(data_group_nsf, leer_scaled_nsf, OutputWorkspace=data_group_nsf.replace('raw', ''))
                CloneWorkspace(data_group_nsf+self.suff_norm,
                               OutputWorkspace=data_group_nsf.replace('raw', '')+self.suff_norm)

                data_group_sf = data_group_sf.replace('raw', '')
                data_group_nsf = data_group_nsf.replace('raw', '')

                self._merge_and_normalize(data_group_sf, self.xax)
                self._merge_and_normalize(data_group_nsf, self.xax)

            if detEffi:
                end_name = 'vcorr_'
            elif flippRatio:
                end_name = 'fcorr_'
            else:
                end_name = ''

            polarisations = []
            row = 0
            while row < sample_table.rowCount():

                pol = sample_table.cell('polarisation', row)
                polarisations.append(pol)

                data_group_sf = sample_table.cell('ws_group', row)
                vana_coefs_total = sample_table.cell('vana_coef_group', row)
                nicr_coef_normalized = sample_table.cell('nicr_coef_group', row)

                data_group_sf = data_group_sf.replace('raw', '')

                print('data group: ', data_group_sf, ", vana_coefs group: ", vana_coefs_total)

                row += offset

                data_group_nsf = sample_table.cell('ws_group', row)

                data_group_nsf = data_group_nsf.replace('raw', '')

                print('data group: ', data_group_nsf)

                row += offset

                if detEffi == "True":

                    data_sf_norm = Multiply(data_group_sf+self.suff_norm, vana_coefs_total,
                                            OutputWorkspace=data_group_sf.replace('group', 'vcorr'+self.suff_norm))
                    data_nsf_norm = Multiply(data_group_nsf+self.suff_norm, vana_coefs_total,
                                             OutputWorkspace=data_group_nsf.replace('group', 'vcorr'+self.suff_norm))

                    for x in self.xax.split(', '):
                        data_sf_merged = DNSMergeRuns(data_group_sf, x, OutputWorkspace=data_group_sf+'_m0')
                        data_nsf_merged = DNSMergeRuns(data_group_nsf, x, OutputWorkspace=data_group_nsf+'_m0')
                        norm_sf_merged = DNSMergeRuns(data_group_sf.replace('group', 'vcorr'+self.suff_norm), x,
                                                      OutputWorkspace=data_group_sf.replace(
                                                          'group', 'vcorr'+self.suff_norm+'_m'))
                        norm_nsf_merged = DNSMergeRuns(data_group_nsf.replace('group','vcorr'+self.suff_norm), x,
                                                       OutputWorkspace=data_group_nsf.replace(
                                                           'group','vcorr'+self.suff_norm+'_m'))
                        Divide(data_sf_merged, norm_sf_merged,
                               OutputWorkspace=data_group_sf.replace('group', 'vcorr_m_'+x))
                        Divide(data_nsf_merged, norm_nsf_merged,
                               OutputWorkspace=data_group_nsf.replace('group', 'vcorr_m_'+x))
                else:

                    data_sf_norm = mtd[data_group_sf+self.suff_norm]
                    data_nsf_norm = mtd[data_group_nsf+self.suff_norm]

                if flippRatio == "True":
                    print(bool(flippRatio))

                    yunit = mtd[nicr_coef_normalized.replace('_normalized', '')].getItem(0).YUnit()

                    data_nratio = Divide(data_nsf_norm, data_sf_norm,
                                         OutputWorkspace=self.out_ws_name+'_data_'+pol+'_nratio')

                    data_sf_scaled = Multiply(data_group_sf, data_nratio, OutputWorkspace=data_group_sf+'_scaled')
                    nicr_corr_step1 = Minus(data_group_nsf, data_sf_scaled,
                                            OutputWorkspace='nicr_'+pol+'_corr_step1')
                    nicr_coor_step2 = Divide(nicr_corr_step1, nicr_coef_normalized,
                                             OutputWorkspace='nicr_'+pol+'_corr_step2')
                    for i in range(nicr_coor_step2.getNumberOfEntries()):
                        nicr_coor_step2.getItem(i).setYUnit(yunit)

                    data_nsf_fcorr = Plus(data_group_nsf, nicr_coor_step2,
                                          OutputWorkspace=data_group_nsf.replace('group', 'fcorr'))
                    data_nsf_fcorr_norm = CloneWorkspace(data_nsf_norm.getName(),
                                                         OutputWorkspace=data_group_nsf.replace(
                                                             'group','fcorr'+self.suff_norm))

                    data_sf_fcorr = Plus(data_group_sf, nicr_coor_step2,
                                         OutputWorkspace=data_group_sf.replace('group', 'fcorr'))
                    data_sf_fcorr_norm = CloneWorkspace(data_sf_norm.getName(),
                                                        OutputWorkspace=data_group_sf.replace(
                                                            'group','fcorr'+self.suff_norm))

                    self._merge_and_normalize(data_nsf_fcorr.getName(), self.xax)
                    self._merge_and_normalize(data_sf_fcorr.getName(), self.xax)

                else:


                if self.sampleParameters["Type"] == 'Polycrystal/Amorphous':
                    print("Polycrystal")
                    if self.sampleParameters['Separation'] == "XYZ":
                        print('XYZ')
                        for x in self.xax.split(', '):
                            print('xax: ', x)
                            spin_incoh = Scale(self.out_ws_name + '_data_' + pol + '_sf_' + end_name + 'm_' + x,
                                               Factor=1.5,
                                               Operation='Multiply',
                                               OutputWorkspace=self.out_ws_name + '_spin_incoh_' + pol + '_' + x)
                            step1first = Scale(self.out_ws_name+'_data_'+pol+'_sf_'+end_name+'m_'+x, Factor=0.5,
                                               Operation='Multiply')

            if self.out_file_directory:
                for pol in polarisations:
                    self._save_to_file('_data_'+pol+'_sf_'+end_name+'m_', self.xax, flipp='_sf', pol='_'+pol)
                    self._save_to_file('_data_'+pol+'_nsf_'+end_name+'m_', self.xax, flipp='_nsf', pol='_'+pol)



AlgorithmFactory.subscribe(DNSProcessSampleData)
