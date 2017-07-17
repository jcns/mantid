from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.simpleapi import Divide, Multiply, Minus, CloneWorkspace, Plus, LoadEmptyInstrument, \
    DeleteWorkspace, DNSMergeRuns, Scale, GroupWorkspaces, RenameWorkspace, ConvertToHistogram, RebinToWorkspace

import numpy as np

import os


class DNSProcessSampleData(PythonAlgorithm):

    def _merge_and_normalize(self, ws_group):
        x_axis = self.xax.split(', ')
        for x in x_axis:
            data_merged = DNSMergeRuns(ws_group, x, OutputWorkspace=ws_group+'_m0'+'_'+x)
            norm_merged = DNSMergeRuns(ws_group+self.suff_norm, x,
                                       OutputWorkspace=ws_group+self.suff_norm+'_m'+'_'+x)

            try:
                Divide(data_merged, norm_merged, OutputWorkspace=ws_group + '_m'+'_'+x)
            except:
                dataX = data_merged.extractX()
                norm_merged.setX(0, dataX[0])
                Divide(data_merged, norm_merged, OutputWorkspace=ws_group+'_m'+'_'+x)

    def _save_to_file(self, file_suffix, flip='', pol='', filename=''):
        axis_dict = {'|Q|': 'Q[A-1]', 'd-Spacing': 'd[A]', '2theta': 'theta[degree]'}
        x_arrays = []
        header = ''
        ws1 = mtd[self.out_ws_name+file_suffix+self.xax.split(', ')[0]]

        for x in self.xax.split(', '):
            ws = mtd[self.out_ws_name+file_suffix+x]

            bin_edges = ws.extractX()[0]
            bin_centers = [(float(bin_edges[i])+float(bin_edges[i+1]))*0.5 for i in range(len(bin_edges)-1)]
            x_arrays.append(np.array(bin_centers))

            if x != '2theta':
                header += axis_dict[x]+'\t\t'
            else:
                header += axis_dict[x]+'\t'

        y = np.array(ws1.extractY()[0])
        err = np.array(ws1.extractE()[0])
        x_arrays.append(y)
        x_arrays.append(err)

        header += 'I\t\tError'
        file_name = os.path.join(self.out_file_directory, self.out_file_prefix+filename+pol+flip+'.txt')
        np.savetxt(file_name, np.transpose(x_arrays), fmt='%1.4e', delimiter='\t', header=header, newline=os.linesep)

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty('SampleTable',              defaultValue='',
                             doc='Name of the sample data ITable Workspace')
        self.declareProperty('SubtractBackground',       defaultValue='',
                             doc='Bool if subtract background for sample')
        self.declareProperty('SubtractBackgroundFactor', defaultValue='', doc='Factor for subtraction of the background')
        self.declareProperty('DeteEffiCorrection',       defaultValue='', doc='Bool if correct detector efficiency')
        self.declareProperty('FlippRatioCorrection',     defaultValue='', doc='Bool if correct flipping ratio')
        self.declareProperty('OutputFileDirectory',      defaultValue='', doc='Directory to save files')
        self.declareProperty('OutputFilePrefix',         defaultValue='', doc='Prefix of the files to save')
        self.declareProperty('OutputWorkspace',          defaultValue='', doc='Name of the output workspace')
        self.declareProperty('OutputXAxis',              defaultValue='', doc='List of the output x axis units')
        self.declareProperty('SampleParameters',         defaultValue='',
                             doc='Dictionary of the parameters for the sample')
        self.declareProperty('Comment',                  defaultValue='', doc='Comment for the output workspace')

    def PyExec(self):

        sample_table = mtd[self.getProperty('SampleTable').value]

        subInst    = self.getProperty('SubtractBackground').value
        detEffi    = self.getProperty('DeteEffiCorrection').value
        flippRatio = self.getProperty('FlippRatioCorrection').value
        if subInst == 'True':
            subInstFac = float(self.getProperty('SubtractBackgroundFactor').value)

        self.out_file_prefix    = self.getProperty('OutputFilePrefix').value
        self.out_file_directory = self.getProperty('OutputFileDirectory').value

        self.out_ws_name = self.getProperty('OutputWorkspace').value
        self.comment     = self.getProperty('Comment').value
        self.xax         = self.getProperty('OutputXAxis').value

        parameters = self.getProperty('SampleParameters').value
        self.sampleParameters = eval(parameters)

        tmp = LoadEmptyInstrument(InstrumentName='DNS')
        self.instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm = self.instrument.getStringParameter('normws_suffix')[0]

        offset = 0
        gr1 = sample_table.cell('ws_group', 0)
        gr2 = sample_table.cell('ws_group', offset)

        while gr1 == gr2:
            offset += 1
            gr2 = sample_table.cell('ws_group', offset)

        self.end_name = '_group'
        if detEffi == 'True':
            self.end_name = '_vcorr'
        if flippRatio == 'True':
            self.end_name = '_fcorr'

        polarisations = []
        row = 0
        self.rebin_ws_name = self.out_ws_name+'_data_'+sample_table.cell('polarisation', 0)+'_sf'+self.end_name+'_m_'

        while row < sample_table.rowCount():

            pol = sample_table.cell('polarisation', row)
            polarisations.append(pol)

            data_group_sf = sample_table.cell('ws_group', row)

            if detEffi == 'True' or flippRatio == 'True' or subInst == 'True':
                bkg_group_sf = sample_table.cell('background_group_ws', row)
            if detEffi == 'True':
                vana_coefs_total = sample_table.cell('vana_coef_group', row)
            if flippRatio == 'True':
                nicr_coef_normalized = sample_table.cell('nicr_coef_group', row)

            row += offset

            data_group_nsf = sample_table.cell('ws_group', row)

            if detEffi == 'True' or flippRatio == 'True' or subInst == 'True':
                bkg_group_nsf = sample_table.cell('background_group_ws', row)

            row += offset

            if subInst == 'True':

                norm_ratio_sf  = Divide(data_group_sf+self.suff_norm, bkg_group_sf+self.suff_norm,
                                        OutputWorkspace=data_group_sf+'_nratio')
                norm_ratio_nsf = Divide(data_group_nsf+self.suff_norm, bkg_group_nsf+self.suff_norm,
                                        OutputWorkspace=data_group_nsf+'_nratio')

                leer_scaled_sf  = Multiply(bkg_group_sf, norm_ratio_sf,
                                           OutputWorkspace=bkg_group_sf.replace('group', 'rawdata'))
                leer_scaled_nsf = Multiply(bkg_group_nsf, norm_ratio_nsf,
                                           OutputWorkspace=bkg_group_nsf.replace('group', 'rawdata'))

                leer_scaled_sf  = Scale(leer_scaled_sf, Factor=subInstFac, Operation='Multiply',
                                        OutputWorkspace=leer_scaled_sf.getName()+'_factor')
                leer_scaled_nsf = Scale(leer_scaled_nsf, Factor=subInstFac, Operation='Multiply',
                                        OutputWorkspace=leer_scaled_nsf.getName()+'_factor')

                Minus(data_group_sf, leer_scaled_sf, OutputWorkspace=data_group_sf.replace('raw', ''))
                CloneWorkspace(data_group_sf+self.suff_norm,
                               OutputWorkspace=data_group_sf.replace('raw', '')+self.suff_norm)

                Minus(data_group_nsf, leer_scaled_nsf, OutputWorkspace=data_group_nsf.replace('raw', ''))
                CloneWorkspace(data_group_nsf+self.suff_norm,
                               OutputWorkspace=data_group_nsf.replace('raw', '')+self.suff_norm)

                data_group_sf  = data_group_sf.replace('raw', '')
                data_group_nsf = data_group_nsf.replace('raw', '')

            else:

                RenameWorkspace(data_group_sf, OutputWorkspace=data_group_sf.replace('raw', ''))
                CloneWorkspace(data_group_sf+self.suff_norm,
                               OutputWorkspace=data_group_sf.replace('raw', '')+self.suff_norm)

                RenameWorkspace(data_group_nsf, OutputWorkspace=data_group_nsf.replace('raw', ''))
                CloneWorkspace(data_group_nsf+self.suff_norm,
                               OutputWorkspace=data_group_nsf.replace('raw', '')+self.suff_norm)

                data_group_sf  = data_group_sf.replace('raw', '')
                data_group_nsf = data_group_nsf.replace('raw', '')

            self._merge_and_normalize(data_group_sf)
            self._merge_and_normalize(data_group_nsf)

            if detEffi == "True":

                data_sf_norm  = Multiply(data_group_sf+self.suff_norm, vana_coefs_total,
                                         OutputWorkspace=data_group_sf.replace('group', 'vcorr'+self.suff_norm))
                data_nsf_norm = Multiply(data_group_nsf+self.suff_norm, vana_coefs_total,
                                         OutputWorkspace=data_group_nsf.replace('group', 'vcorr'+self.suff_norm))

                for x in self.xax.split(', '):
                    data_sf_merged  = DNSMergeRuns(data_group_sf, x, OutputWorkspace=data_group_sf+'_m0')
                    data_nsf_merged = DNSMergeRuns(data_group_nsf, x, OutputWorkspace=data_group_nsf+'_m0')
                    norm_sf_merged  = DNSMergeRuns(data_group_sf.replace('group', 'vcorr'+self.suff_norm), x,
                                                   OutputWorkspace=data_group_sf.replace(
                                                       'group', 'vcorr'+self.suff_norm+'_m_'+x))
                    norm_nsf_merged = DNSMergeRuns(data_group_nsf.replace('group', 'vcorr'+self.suff_norm), x,
                                                   OutputWorkspace=data_group_nsf.replace(
                                                       'group', 'vcorr'+self.suff_norm+'_m_'+x))

                    Divide(data_sf_merged, norm_sf_merged,
                           OutputWorkspace=data_group_sf.replace('group', 'vcorr_m_'+x))
                    Divide(data_nsf_merged, norm_nsf_merged,
                           OutputWorkspace=data_group_nsf.replace('group', 'vcorr_m_'+x))
            else:

                data_sf_norm  = CloneWorkspace(data_group_sf+self.suff_norm,
                                               OutputWorkspace=data_group_sf.replace('group',
                                                                                     'vcorr'+self.suff_norm))
                data_nsf_norm = CloneWorkspace(data_group_nsf+self.suff_norm,
                                               OutputWorkspace=data_group_nsf.replace('group',
                                                                                      'vcorr'+self.suff_norm))

            data_nratio = Divide(data_nsf_norm, data_sf_norm,
                                 OutputWorkspace=self.out_ws_name+'_data_'+pol+'_nratio')

            if flippRatio == "True":

                yunit = mtd[nicr_coef_normalized.replace('_normalized', '')].getItem(0).YUnit()

                data_sf_scaled = Multiply(data_group_sf, data_nratio, OutputWorkspace=data_group_sf+'_scaled')

                nicr_corr_step1 = Minus(data_group_nsf, data_sf_scaled,
                                        OutputWorkspace=self.out_ws_name+'_nicr_'+pol+'_corr_step1')
                nicr_coor_step2 = Divide(nicr_corr_step1, nicr_coef_normalized,
                                         OutputWorkspace=self.out_ws_name+'_nicr_'+pol+'_corr_step2')

                for i in range(nicr_coor_step2.getNumberOfEntries()):
                    nicr_coor_step2.getItem(i).setYUnit(yunit)

                data_nsf_fcorr      = Plus(data_group_nsf, nicr_coor_step2,
                                           OutputWorkspace=data_group_nsf.replace('group', 'fcorr'))
                CloneWorkspace(data_nsf_norm.getName(),
                               OutputWorkspace=data_group_nsf.replace('group', 'fcorr'+self.suff_norm))

                data_sf_fcorr      = Minus(data_group_sf, nicr_coor_step2,
                                           OutputWorkspace=data_group_sf.replace('group', 'fcorr'))
                CloneWorkspace(data_sf_norm.getName(),
                               OutputWorkspace=data_group_sf.replace('group', 'fcorr'+self.suff_norm))
            else:

                data_sf_fcorr = mtd[data_group_sf]
                data_nsf_fcorr = mtd[data_group_nsf]

            self._merge_and_normalize(data_sf_fcorr.getName())
            self._merge_and_normalize(data_nsf_fcorr.getName())

            for x in self.xax.split(', '):

                data_sf_ax_name       = self.out_ws_name+'_data_'+pol+'_sf'+self.end_name+'_m_'+x
                data_nsf_ax_name      = self.out_ws_name+'_data_'+pol+'_nsf'+self.end_name+'_m_'+x
                data_sf_norm_ax_name  = self.out_ws_name+'_data_'+pol+'_sf'+self.end_name +\
                                        self.suff_norm+'_m_'+x
                data_nsf_norm_ax_name = self.out_ws_name+'_data_'+pol+'_nsf'+self.end_name + \
                                        self.suff_norm+'_m_' + x

                data_sf_ax       = ConvertToHistogram(data_sf_ax_name,       OutputWorkspace=data_sf_ax_name)
                data_nsf_ax      = ConvertToHistogram(data_nsf_ax_name,      OutputWorkspace=data_nsf_ax_name)
                data_sf_norm_ax  = ConvertToHistogram(data_sf_norm_ax_name,  OutputWorkspace=data_sf_norm_ax_name)
                data_nsf_norm_ax = ConvertToHistogram(data_nsf_norm_ax_name, OutputWorkspace=data_nsf_norm_ax_name)

                RebinToWorkspace(data_sf_ax,       self.rebin_ws_name+x, OutputWorkspace=data_sf_ax.getName())
                RebinToWorkspace(data_nsf_ax,      self.rebin_ws_name+x, OutputWorkspace=data_nsf_ax.getName())
                RebinToWorkspace(data_sf_norm_ax,  self.rebin_ws_name+x, OutputWorkspace=data_sf_norm_ax.getName())
                RebinToWorkspace(data_nsf_norm_ax, self.rebin_ws_name+x, OutputWorkspace=data_nsf_norm_ax.getName())

            if self.sampleParameters["Type"] == 'Polycrystal/Amorphous':
                if self.sampleParameters['Separation'] == "Coherent/Incoherent":
                    outws_group = []
                    for x in self.xax.split(', '):
                        print(x)
                        print(self.rebin_ws_name+x)
                        spin_incoh = Scale(self.out_ws_name+'_data_'+pol+'_sf'+self.end_name+'_m_'+x,
                                           Factor=1.5,
                                           Operation='Multiply',
                                           OutputWorkspace=self.out_ws_name+'_spin_incoh_'+pol+'_'+x)

                        step1     = 0.5*data_sf_fcorr*data_nratio
                        coh_group = data_nsf_fcorr-step1

                        RenameWorkspace(coh_group, OutputWorkspace=self.out_ws_name+'_coh_group_'+pol+'_'+x)
                        RenameWorkspace(step1,     OutputWorkspace='step1_'+pol+'_'+x)

                        nuclear_coh_merged = DNSMergeRuns(self.out_ws_name+'_coh_group_'+pol+'_'+x, x,
                                                          OutputWorkspace=self.out_ws_name+'_nuclear_coh_merged_'+pol +
                                                                           '_'+x)

                        nuclear_coh_merged = ConvertToHistogram(nuclear_coh_merged,
                                                                OutputWorkspace=nuclear_coh_merged.getName())


                        nuclear_coh_merged = RebinToWorkspace(nuclear_coh_merged, self.rebin_ws_name+x,
                                                              OutputWorkspace=nuclear_coh_merged.getName())

                        nuclear_coh = Divide(nuclear_coh_merged,
                                             self.out_ws_name+'_data_'+pol+'_nsf'+self.end_name +
                                             self.suff_norm+'_m_'+x,
                                             OutputWorkspace=self.out_ws_name+'_nuclear_coh_'+pol+'_'+x)

                        outws = Divide(nuclear_coh, spin_incoh,
                                       OutputWorkspace=self.out_ws_name+'_ratio_'+pol+'_'+x)
                        outws.setComment(self.comment)
                        outws_group.append(outws)

                    GroupWorkspaces(outws_group, OutputWorkspace=self.out_ws_name+'_ratio_'+pol)

                    if self.out_file_directory:
                        self._save_to_file('_nuclear_coh_'+pol+'_', pol='_'+pol, filename='_coh')
                        self._save_to_file('_spin_incoh_'+pol+'_',  pol='_'+pol, filename='_incoh')
                        self._save_to_file('_ratio_'+pol+'_',       pol='_'+pol, filename='_ratio')

        if self.sampleParameters['Type'] == 'Polycrystal/Amorphous':
            if self.sampleParameters['Separation'] == 'XYZ':
                for x in self.xax.split(', '):
                    xsf  = CloneWorkspace(mtd[self.out_ws_name+'_data_x_sf'+self.end_name+'_m_'+x])
                    ysf  = CloneWorkspace(mtd[self.out_ws_name+'_data_y_sf'+self.end_name+'_m_'+x])
                    zsf  = CloneWorkspace(mtd[self.out_ws_name+'_data_z_sf'+self.end_name+'_m_'+x])
                    znsf = CloneWorkspace(mtd[self.out_ws_name+'_data_z_nsf'+self.end_name+'_m_'+x])

                    magnetic    = 2.0*(xsf + ysf - 2.0*zsf)
                    spin_incoh  = (3/2)*(3.0*zsf - xsf - ysf)
                    nuclear_coh = znsf - (1/2)*magnetic - (1/3)*spin_incoh

                    nuclear_coh.setComment(self.comment)

                    for wname in ['magnetic', 'spin_incoh', 'nuclear_coh', 'xsf', 'ysf', 'zsf', 'znsf']:
                        RenameWorkspace(wname, self.out_ws_name+'_'+wname+'_'+x)

                if self.out_file_directory:
                    self._save_to_file('_magnetic_',    filename='_magnetic')
                    self._save_to_file('_spin_incoh_',  filename='_incoh')
                    self._save_to_file('_nuclear_coh_', filename='_coh')

        if self.out_file_directory:
            for pol in polarisations:
                self._save_to_file('_data_' + pol +'_sf' + self.end_name +'_m_', flip='_sf', pol='_' + pol)
                self._save_to_file('_data_' + pol +'_nsf' + self.end_name +'_m_', flip='_nsf', pol='_' + pol)



AlgorithmFactory.subscribe(DNSProcessSampleData)
