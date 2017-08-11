from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd, Projection
from mantid.simpleapi import Divide, Multiply, Minus, CloneWorkspace, Plus, LoadEmptyInstrument, SetUB, AddSampleLog,\
    DeleteWorkspace, DNSMergeRuns, Scale, GroupWorkspaces, RenameWorkspace, ConvertToHistogram, RebinToWorkspace, \
    SetGoniometer, ConvertToDiffractionMDWorkspace, CutMD, SmoothMD, BinMD,ConvertMDHistoToMatrixWorkspace, DivideMD
import mantidplot
import numpy as np

import os


class DNSProcessSampleData(PythonAlgorithm):
    """
    Correct and reduce sample data
    """

    def __init__(self):
        PythonAlgorithm.__init__(self)

        self.bkg_group_sf  = ""
        self.bkg_group_nsf = ""

        self.comment = ""

        self.data_group_sf  = ""
        self.data_group_nsf = ""

        self.data_sf_norm  = ""
        self.data_nsf_norm = ""

        self.data_sf_fcorr  = ""
        self.data_nsf_fcorr = ""

        self.end_name = ""

        self.keep_events = False

        self.nicr_coef_normalized = ""

        self.omegas_data = []

        self.out_ws_name = ""

        self.out_file_directory = ""
        self.out_file_prefix    = ""

        self.polarisations = []

        self.rebin_ws_name = ""

        self.sampleParameters = {}

        self.sc = False

        self.suff_norm = ""

        self.vana_coefs_total = ""

        self.xax = ""

        self._m_and_n = False

    def _merge_and_normalize(self, ws_group):
        """
        merge and normalize workspace group for all output x axis units
        :param ws_group: workspace group
        """
        x_axis = self.xax.split(", ")
        for x in x_axis:
            data_merged = DNSMergeRuns(ws_group, x, OutputWorkspace=ws_group+"_m0_"+x)
            norm_merged = DNSMergeRuns(ws_group+self.suff_norm, x, OutputWorkspace=ws_group+self.suff_norm+"_m_"+x)
            try:
                Divide(data_merged, norm_merged, OutputWorkspace=ws_group+"_m_"+x)
            except:
                dataX = data_merged.extractX()
                norm_merged.setX(0, dataX[0])
                Divide(data_merged, norm_merged, OutputWorkspace=ws_group+"_m_"+x)

    def _save_to_file(self, file_suffix, flip="", pol="", filename=""):
        """
        save workspace to file
        :param file_suffix: suffix of workspace name to be saved
        :param flip: flip or none spin flip 
        :param pol: polarisation of the workspace to be saved
        :param filename: name of the file
        """
        # headers for x axis units
        axis_dict = {"|Q|": "Q[A-1]", "d-Spacing": "d[A]", "2theta": "theta[degree]"}
        x_arrays  = []
        header    = ""

        ws1 = mtd[self.out_ws_name+file_suffix+self.xax.split(", ")[0]]

        # column for every x axis unit with x values
        for x in self.xax.split(", "):
            ws = mtd[self.out_ws_name+file_suffix+x]

            bin_edges   = ws.extractX()[0]
            bin_centers = [(float(bin_edges[i])+float(bin_edges[i+1]))*0.5 for i in range(len(bin_edges)-1)]
            x_arrays.append(np.array(bin_centers))

            if x != "2theta" and "d-Spacing" in self.xax.split(", "):
                header += axis_dict[x]+"\t\t"
            else:
                header += axis_dict[x]+"\t"

        # y and error values
        y   = np.array(ws1.extractY()[0])
        err = np.array(ws1.extractE()[0])
        x_arrays.append(y)
        x_arrays.append(err)
        # header for intensities (y) and errors
        header += "I\t\tError"

        # save data in file
        file_name = os.path.join(self.out_file_directory, self.out_file_prefix+filename+pol+flip+".txt")
        np.savetxt(file_name, np.transpose(x_arrays), fmt="%1.4e", delimiter="\t", header=header, newline=os.linesep)

    def _save_md_to_file(self, flip="", pol=""):
        """
        save multi dimensional workspace to file
        :param flip: non spin flip/ spin fip
        :param pol: polarisation of the workspace
        """
        header = ""

        ws = mtd[self.out_ws_name+"_sc_"+pol+flip+"_proj_res"]

        header += "# x\t\ty\t\tI\n"

        file_name = os.path.join(self.out_file_directory, self.out_file_prefix+"_sc_"+pol+flip)

        # create arrays for x values, y values and intensity
        I_array = ws.getSignalArray()
        x_arrays = []
        for i in range(ws.getDimension(0).getNBins()):
            x = []
            y = []
            I = []
            _array = []
            for j in range(ws.getDimension(1).getNBins()):
                x.append(ws.getDimension(0).getX(i))
                y.append(ws.getDimension(1).getX(j))
                I.append(I_array[i][j][0])
            _array.append(x)
            _array.append(y)
            _array.append(I)
            x_arrays.append(_array)

        # write data to file
        with open(file_name, "w") as f:
            f.write(header)
            for a in x_arrays:
                np.savetxt(f, np.transpose(a), fmt="%1.4e", delimiter="\t")
                f.write("\n")

    def _get_offset(self, sample_table):
        """
        compute offset to next workspace group
        :param sample_table: sample data table
        :return: offset to next workspace group
        """
        offset = 0

        gr1 = sample_table.cell("ws_group", 0)
        gr2 = sample_table.cell("ws_group", offset)

        while gr1 == gr2:
            offset += 1
            gr2 = sample_table.cell("ws_group", offset)

        return offset

    def _get_end_name(self, detEffi, flipRatio):
        """
        name of the corrected workspace
        :param detEffi: Boolean if detector efficiency correction
        :param flipRatio: Boolean if flipping ratio correction
        """
        self.end_name = "_group"
        if detEffi:
            self.end_name = "_vcorr"
        if flipRatio:
            self.end_name = "_fcorr"

    def _do_correction(self, sample_table, detEffi, flipRatio, subInst, subInstFac, omegas):
        """
        correction of sample data
        :param sample_table: table of sample data
        :param detEffi: boolean if detector efficiency correction
        :param flipRatio: boolean if flipping ratio correction
        :param subInst: boolean if subtract instrument background for sample data
        :param subInstFac: Factor for subtract instrument background for sample data
        """
        row = 0

        # compute offset
        offset = self._get_offset(sample_table)
        # offset to nsf workspace from sf workspace for single crystal samples
        if self.sc:
            offsetnsf = offset*len(omegas)

        while row < sample_table.rowCount() and sample_table.cell("flipper", row) == "ON":

            pol = sample_table.cell("polarisation", row)
            if pol not in self.polarisations:
                self.polarisations.append(pol)

            if self.sc:
                omega = sample_table.cell("omega", row)
                if omega not in self.omegas_data:
                    self.omegas_data.append(omega)

            # spin flip

            self.data_group_sf = sample_table.cell("ws_group", row)
            print(self.data_group_sf)

            # get background and coefficients if needed
            if detEffi or flipRatio or subInst:
                self.bkg_group_sf = sample_table.cell("background_group_ws", row)
            if detEffi:
                self.vana_coefs_total = sample_table.cell("vana_coef_group", row)
            if flipRatio:
                self.nicr_coef_normalized = sample_table.cell("nicr_coef_group", row)

            if self.sc:
                rowsf = row
                row   = row+offsetnsf
            else:
                row += offset

            # non spin flip

            self.data_group_nsf = sample_table.cell("ws_group", row)
            print(self.data_group_nsf)

            if detEffi or flipRatio or subInst:
                self.bkg_group_nsf = sample_table.cell("background_group_ws", row)

            if self.sc:
                row = rowsf + offset
            else:
                row += offset

            # correct data
            if self.sc:
                self._correction(pol, subInst, subInstFac, detEffi, flipRatio, omega)
            else:
                self._correction(pol, subInst, subInstFac, detEffi, flipRatio)

    def _correction(self, pol, subInst, subInstFac, detEffi, flipRatio, omega=""):
        """
        correct and reduce data
        :param pol: polarisation of this workspaces
        :param subInst: Boolean if subtract instrument background
        :param subInstFac: Factor for instrument background subtraction
        :param detEffi: Boolean if detector efficiency correction
        :param flipRatio: Boolean if flipping ratio correction
        :param omega: omega of this workspaces
        :return: 
        """

        # subtract instrument background
        if subInst:
            self.sub_inst_bkg(subInstFac, omega)
        else:
            self._not_sub_inst_bkg()

        # merge and normalize workspaces
        if self._m_and_n and not self.sc:
            self._merge_and_normalize(self.data_group_sf)
            self._merge_and_normalize(self.data_group_nsf)

        # detector efficiency correction
        if detEffi:
            self._det_effi_corr()
        else:
            self._no_det_effi_corr()

        # norm ratio workspaces
        if self.sc:
            data_nratio = Divide(self.data_nsf_norm, self.data_sf_norm,
                                 OutputWorkspace=self.out_ws_name+"_data_"+pol+"_omega_"+omega+"_nratio")
        else:
            data_nratio = Divide(self.data_nsf_norm, self.data_sf_norm,
                                 OutputWorkspace=self.out_ws_name+"_data_"+pol+"_nratio")

        # flipping ratio correction
        if flipRatio:
            self._flipping_ratio_corr(data_nratio, pol, omega)
        else:
            if self.sc:
                self._no_flipping_ratio_corr()
            else:
                self.data_sf_fcorr  = self.data_group_sf
                self.data_nsf_fcorr = self.data_group_nsf

        # merge and normalize corrected workspaces
        if self._m_and_n and not self.sc:
            self._merge_and_normalize(self.data_sf_fcorr.getName())
            self._merge_and_normalize(self.data_nsf_fcorr.getName())

        # rebin workspaces
        self._rebin_ws(pol)

        # calculate coherent separation
        if self.sampleParameters["Type"] == "Polycrystal/Amorphous":
            if self.sampleParameters["Separation"] == "Coherent/Incoherent":
                self._coherent_separation(pol, self.data_sf_fcorr, self.data_nsf_fcorr, data_nratio)

    def sub_inst_bkg(self, subInstFac, omega):
        """
        subtract instrument background for sample data
        :param subInstFac: Factor for instrument background subtraction
        :param omega: omega of this workspace (for single crystal sample)
        """
        norm_ratio_sf  = Divide(self.data_group_sf+self.suff_norm, self.bkg_group_sf+self.suff_norm,
                                OutputWorkspace=self.data_group_sf+"_nratio")
        norm_ratio_nsf = Divide(self.data_group_nsf+self.suff_norm, self.bkg_group_nsf+self.suff_norm,
                                OutputWorkspace=self.data_group_nsf+"_nratio")

        if self.sc:
            leer_scaled_sf  = Multiply(self.bkg_group_sf, norm_ratio_sf,
                                       OutputWorkspace=self.bkg_group_sf.replace("group", "rawdata_omega_"+omega))
            leer_scaled_nsf = Multiply(self.bkg_group_nsf, norm_ratio_nsf,
                                       OutputWorkspace=self.bkg_group_nsf.replace("group", "rawdata_omega_"+omega))
        else:
            leer_scaled_sf  = Multiply(self.bkg_group_sf, norm_ratio_sf,
                                       OutputWorkspace=self.bkg_group_sf.replace("group", "rawdata"))
            leer_scaled_nsf = Multiply(self.bkg_group_nsf, norm_ratio_nsf,
                                       OutputWorkspace=self.bkg_group_nsf.replace("group", "rawdata"))

        leer_scaled_sf  = Scale(leer_scaled_sf, Factor=subInstFac, Operation="Multiply",
                                OutputWorkspace=leer_scaled_sf.getName()+"_factor")
        leer_scaled_nsf = Scale(leer_scaled_nsf, Factor=subInstFac, Operation="Multiply",
                                OutputWorkspace=leer_scaled_nsf.getName()+"_factor")

        Minus(self.data_group_sf, leer_scaled_sf, OutputWorkspace=self.data_group_sf.replace("raw", ""))
        CloneWorkspace(self.data_group_sf+self.suff_norm,
                       OutputWorkspace=self.data_group_sf.replace("raw", "")+self.suff_norm)

        Minus(self.data_group_nsf, leer_scaled_nsf, OutputWorkspace=self.data_group_nsf.replace("raw", ""))
        CloneWorkspace(self.data_group_nsf+self.suff_norm,
                       OutputWorkspace=self.data_group_nsf.replace("raw", "")+self.suff_norm)

        self.data_group_sf  = self.data_group_sf.replace("raw", "")
        self.data_group_nsf = self.data_group_nsf.replace("raw", "")

    def _not_sub_inst_bkg(self):
        """
        rename workspaces, for further calculations
        """
        RenameWorkspace(self.data_group_sf, OutputWorkspace=self.data_group_sf.replace("raw", ""))
        CloneWorkspace(self.data_group_sf+self.suff_norm,
                       OutputWorkspace=self.data_group_sf.replace("raw", "")+self.suff_norm)

        RenameWorkspace(self.data_group_nsf, OutputWorkspace=self.data_group_nsf.replace("raw", ""))
        CloneWorkspace(self.data_group_nsf+self.suff_norm,
                       OutputWorkspace=self.data_group_nsf.replace("raw", "")+self.suff_norm)

        self.data_group_sf  = self.data_group_sf.replace("raw", "")
        self.data_group_nsf = self.data_group_nsf.replace("raw", "")

    def _det_effi_corr(self):
        """
        detector efficiency correction
        """
        self.data_sf_norm  = Multiply(self.data_group_sf+self.suff_norm, self.vana_coefs_total,
                                      OutputWorkspace=self.data_group_sf.replace("group", "vcorr"+self.suff_norm))
        self.data_nsf_norm = Multiply(self.data_group_nsf+self.suff_norm, self.vana_coefs_total,
                                      OutputWorkspace=self.data_group_nsf.replace("group", "vcorr"+self.suff_norm))

        if not self.sc or self.sc and mtd[self.data_group_sf].getNumberOfEntries() >= 2:
            for x in self.xax.split(", "):
                data_sf_merged  = DNSMergeRuns(self.data_group_sf, x, OutputWorkspace=self.data_group_sf+"_m0")
                data_nsf_merged = DNSMergeRuns(self.data_group_nsf, x, OutputWorkspace=self.data_group_nsf+"_m0")
                norm_sf_merged  = DNSMergeRuns(self.data_group_sf.replace("group", "vcorr"+self.suff_norm), x,
                                               OutputWorkspace=self.data_group_sf.replace(
                                                   "group", "vcorr"+self.suff_norm+"_m_"+x))
                norm_nsf_merged = DNSMergeRuns(self.data_group_nsf.replace("group", "vcorr"+self.suff_norm), x,
                                               OutputWorkspace=self.data_group_nsf.replace(
                                                   "group", "vcorr"+self.suff_norm+"_m_"+x))

                Divide(data_sf_merged, norm_sf_merged,
                       OutputWorkspace=self.data_group_sf.replace("group", "vcorr_m_"+x))
                Divide(data_nsf_merged, norm_nsf_merged,
                       OutputWorkspace=self.data_group_nsf.replace("group", "vcorr_m_"+x))

        self.data_group_sf  = CloneWorkspace(self.data_group_sf,
                                             OutputWorkspace=self.data_group_sf.replace("group", "vcorr"))
        self.data_group_nsf = CloneWorkspace(self.data_group_nsf,
                                             OutputWorkspace=self.data_group_nsf.replace("group", "vcorr"))

    def _no_det_effi_corr(self):
        """
        Clone workspaces for futher calculations
        """
        self.data_sf_norm  = CloneWorkspace(self.data_group_sf+self.suff_norm,
                                            OutputWorkspace=self.data_group_sf.replace("group",
                                                                                       "vcorr"+self.suff_norm))
        self.data_nsf_norm = CloneWorkspace(self.data_group_nsf+self.suff_norm,
                                            OutputWorkspace=self.data_group_nsf.replace("group",
                                                                                        "vcorr"+self.suff_norm))

        self.data_group_sf  = CloneWorkspace(self.data_group_sf,
                                             OutputWorkspace=self.data_group_sf.replace("group", "vcorr"))
        self.data_group_nsf = CloneWorkspace(self.data_group_nsf,
                                             OutputWorkspace=self.data_group_nsf.replace("group", "vcorr"))

    def _flipping_ratio_corr(self, nratio, pol, omega):
        """
        flipping ratio correction
        :param nratio: norm ratio workspace
        :param pol: polarisation of the workspaces 
        :param omega: omega of the workspaces (for single crystal sample)
        """
        yunit = mtd[self.nicr_coef_normalized.replace("_normalized", "")].getItem(0).YUnit()

        data_sf_scaled = Multiply(self.data_group_sf, nratio, OutputWorkspace=self.data_group_sf.getName()+"_scaled")
        if self.sc:
            nicr_corr_step1 = Minus(self.data_group_nsf, data_sf_scaled,
                                    OutputWorkspace=self.out_ws_name+"_nicr_"+pol+"_omega_"+omega+"_corr_step1")
            nicr_coor_step2 = Divide(nicr_corr_step1, self.nicr_coef_normalized,
                                     OutputWorkspace=self.out_ws_name+"_nicr_"+pol+"_omega_"+omega+"_corr_step2")
        else:
            nicr_corr_step1 = Minus(self.data_group_nsf, data_sf_scaled,
                                    OutputWorkspace=self.out_ws_name+"_nicr_"+pol+"_corr_step1")
            nicr_coor_step2 = Divide(nicr_corr_step1, self.nicr_coef_normalized,
                                     OutputWorkspace=self.out_ws_name+"_nicr_"+pol+"_corr_step2")

        # set y unit for the workspace
        for i in range(nicr_coor_step2.getNumberOfEntries()):
            nicr_coor_step2.getItem(i).setYUnit(yunit)

        data_group_nsf_name = self.data_group_nsf.getName()
        self.data_nsf_fcorr = Plus(self.data_group_nsf, nicr_coor_step2,
                                   OutputWorkspace=data_group_nsf_name.replace("vcorr", "fcorr"))
        self.data_nsf_norm  = CloneWorkspace(self.data_nsf_norm,
                                             OutputWorkspace=data_group_nsf_name.replace("vcorr", "fcorr"+
                                                                                                       self.suff_norm))
        data_group_sf_name = self.data_group_sf.getName()
        self.data_sf_fcorr = Minus(self.data_group_sf, nicr_coor_step2,
                                   OutputWorkspace=data_group_sf_name.replace("vcorr", "fcorr"))
        for i in range(20):
            print("\n")
        print("data group type: ", type(self.data_group_sf))
        self.data_sf_norm  = CloneWorkspace(self.data_sf_norm.getName(),
                                            OutputWorkspace=data_group_sf_name.replace("vcorr","fcorr"+
                                                                                                    self.suff_norm))

    def _no_flipping_ratio_corr(self):
        """
        clone workspaces for further calculations
        """
        self.data_nsf_fcorr = CloneWorkspace(self.data_group_nsf,
                                             OutputWorkspace=self.data_group_nsf.getName().replace("vcorr", "fcorr"))
        self.data_nsf_norm  = CloneWorkspace(self.data_nsf_norm,
                                             OutputWorkspace=self.data_group_nsf.getName().replace("vcorr", "fcorr"+
                                                                                                   self.suff_norm))
        self.data_sf_fcorr = CloneWorkspace(self.data_group_sf,
                                            OutputWorkspace=self.data_group_sf.getName().replace("vcorr", "fcorr"))
        self.data_sf_norm  = CloneWorkspace(self.data_sf_norm.getName(),
                                            OutputWorkspace=self.data_group_sf.getName().replace("vcorr", "fcorr"+
                                                                                                 self.suff_norm))

    def _rebin_ws(self, pol):
        """
        rebin workspaces
        :param pol: polarisations of this workspaces
        """
        if not self.sc:
            for x in self.xax.split(", "):
                data_sf_ax_name       = self.out_ws_name+"_data_"+pol+"_sf"+self.end_name+"_m_"+x
                data_nsf_ax_name      = self.out_ws_name+"_data_"+pol+"_nsf"+self.end_name+"_m_"+x
                data_sf_norm_ax_name  = self.out_ws_name+"_data_"+pol+"_sf"+self.end_name+self.suff_norm+"_m_"+x
                data_nsf_norm_ax_name = self.out_ws_name+"_data_"+pol+"_nsf"+self.end_name+self.suff_norm+"_m_"+x

                data_sf_ax       = ConvertToHistogram(data_sf_ax_name,       OutputWorkspace=data_sf_ax_name)
                data_nsf_ax      = ConvertToHistogram(data_nsf_ax_name,      OutputWorkspace=data_nsf_ax_name)
                data_sf_norm_ax  = ConvertToHistogram(data_sf_norm_ax_name,  OutputWorkspace=data_sf_norm_ax_name)
                data_nsf_norm_ax = ConvertToHistogram(data_nsf_norm_ax_name, OutputWorkspace=data_nsf_norm_ax_name)

                RebinToWorkspace(data_sf_ax,       self.rebin_ws_name+x, OutputWorkspace=data_sf_ax.getName())
                RebinToWorkspace(data_nsf_ax,      self.rebin_ws_name+x, OutputWorkspace=data_nsf_ax.getName())
                RebinToWorkspace(data_sf_norm_ax,  self.rebin_ws_name+x, OutputWorkspace=data_sf_norm_ax.getName())
                RebinToWorkspace(data_nsf_norm_ax, self.rebin_ws_name+x, OutputWorkspace=data_nsf_norm_ax.getName())

    def _no_separation(self):
        """
        set comments to corrected workspaces
        """
        ws_group = []
        for pol in self.polarisations:
            for flip in ["sf", "nsf"]:
                for x in self.xax.split(", "):
                    ws = mtd[self.out_ws_name+"_data_"+pol+"_"+flip+self.end_name+"_m_"+x]
                    ws.setComment(self.comment)
                    ws_group.append(ws)
        GroupWorkspaces(ws_group, OutputWorkspace=self.out_ws_name)

    def _xyz_separation(self):
        """
        'XYZ' separation: calculate magnetic, spin incoherent and nuclear coherent
        set comment to nuclear coherent -> result workspace
        """
        ws_group = []
        for x in self.xax.split(", "):
            xsf  = CloneWorkspace(mtd[self.out_ws_name+"_data_x_sf"+self.end_name+"_m_"+x])
            ysf  = CloneWorkspace(mtd[self.out_ws_name+"_data_y_sf"+self.end_name+"_m_"+x])
            zsf  = CloneWorkspace(mtd[self.out_ws_name+"_data_z_sf"+self.end_name+"_m_"+x])
            znsf = CloneWorkspace(mtd[self.out_ws_name+"_data_z_nsf"+self.end_name+"_m_"+x])

            magnetic    = 2.0*(xsf + ysf - 2.0*zsf)
            spin_incoh  = (3/2)*(3.0*zsf - xsf - ysf)
            nuclear_coh = znsf - (1/2)*magnetic - (1/3)*spin_incoh

            nuclear_coh.setComment(self.comment)

            for wname in ["magnetic", "spin_incoh", "nuclear_coh", "xsf", "ysf", "zsf", "znsf"]:
                ws = RenameWorkspace(wname, OutputWorkspace=self.out_ws_name+"_"+wname+"_"+x)
                ws_group.append(ws)

        GroupWorkspaces(ws_group, OutputWorkspace=self.out_ws_name)

        # save result workspaces to file
        if self.out_file_directory:
            self._save_to_file("_magnetic_",    filename="_magnetic")
            self._save_to_file("_spin_incoh_",  filename="_incoh")
            self._save_to_file("_nuclear_coh_", filename="_coh")

    def _coherent_separation(self, pol, sf_fcorr, nsf_fcorr, nratio):
        """
        'Coherent/Incoherent' separation: calculate spin incoherent, nuclear coherent and ratio 
        for this polarisation
        :param pol: polarisation for this workspaces
        :param sf_fcorr: corrected spin flip workspace
        :param nsf_fcorr: corrected non spin flip workspace
        :param nratio: norm ratio workspace
        """
        ws_group = []
        outws_group = []
        for x in self.xax.split(", "):
            spin_incoh = Scale(self.out_ws_name+"_data_"+pol+"_sf"+self.end_name+"_m_"+x,
                               Factor=1.5,
                               Operation="Multiply",
                               OutputWorkspace=self.out_ws_name+"_spin_incoh_"+pol+"_"+x)
            ws_group.append(spin_incoh)

            step1     = 0.5*sf_fcorr*nratio
            coh_group = nsf_fcorr-step1

            RenameWorkspace(coh_group, OutputWorkspace=self.out_ws_name+"_coh_group_"+pol+"_"+x)
            RenameWorkspace(step1,     OutputWorkspace="step1_"+pol+"_"+x)

            nuclear_coh_merged = DNSMergeRuns(self.out_ws_name+"_coh_group_"+pol+"_"+x, x,
                                              OutputWorkspace=self.out_ws_name+"_nuclear_coh_merged_"+pol+"_"+x)

            nuclear_coh_merged = ConvertToHistogram(nuclear_coh_merged,
                                                    OutputWorkspace=nuclear_coh_merged.getName())

            nuclear_coh_merged = RebinToWorkspace(nuclear_coh_merged, self.rebin_ws_name+x,
                                                  OutputWorkspace=nuclear_coh_merged.getName())

            nuclear_coh = Divide(nuclear_coh_merged,
                                 self.out_ws_name+"_data_"+pol+"_nsf"+self.end_name+self.suff_norm+"_m_"+x,
                                 OutputWorkspace=self.out_ws_name+"_nuclear_coh_"+pol+"_"+x)
            ws_group.append(nuclear_coh)

            outws = Divide(nuclear_coh, spin_incoh,
                           OutputWorkspace=self.out_ws_name+"_ratio_"+pol+"_"+x)
            outws.setComment(self.comment)
            outws_group.append(outws)
            ws_group.append(outws)

        GroupWorkspaces(outws_group, OutputWorkspace=self.out_ws_name+"_ratio_"+pol)
        GroupWorkspaces(ws_group, OutputWorkspace=self.out_ws_name)

        # save result workspaces to file
        if self.out_file_directory:
            self._save_to_file("_nuclear_coh_"+pol+"_", pol="_"+pol, filename="_coh")
            self._save_to_file("_spin_incoh_"+pol+"_",  pol="_"+pol, filename="_incoh")
            self._save_to_file("_ratio_"+pol+"_",       pol="_"+pol, filename="_ratio")

    def _single_crystal_correction(self):
        """
        correction for single crystal sample
        """
        end_group = []

        lattice = self.sampleParameters["Lattice parameters"]
        scatter = self.sampleParameters["Scattering Plane"]

        u = [float(u) for u in scatter["u"].split(", ")]
        v = [-1*float(v) for v in scatter["v"].split(", ") if v != 0.0]

        # create projection workspace
        projection = Projection(u, v)
        proj_ws    = projection.createWorkspace()

        for flip in ["_sf", "_nsf"]:
            for pol in self.polarisations:
                result_name      = self.out_ws_name+"_sc_"+pol+flip
                result_name_norm = self.out_ws_name+"_sc_"+pol+flip+self.suff_norm
                for omega in self.omegas_data:
                    input_name      = self.out_ws_name+"_data_"+pol+flip+"_omega_"+omega+"_fcorr"
                    ws_group        = mtd[input_name]
                    input_name_norm = self.out_ws_name+"_data_"+pol+flip+"_omega_"+omega+"_fcorr"+self.suff_norm
                    ws_group_norm   = mtd[input_name_norm]

                    # set ub and goniometer for all workspaces of this group and append them to a
                    # multidimensional workspace (for data workspace group and norm workspace group
                    for i in range(ws_group.getNumberOfEntries()):
                        ws      = ws_group.getItem(i)
                        ws_norm = ws_group_norm.getItem(i)

                        SetUB(ws, a=float(lattice["a"]), b=float(lattice["b"]), c=float(lattice["c"]),
                              u=scatter["u"], v=scatter["v"], alpha=float(lattice["alpha"]),
                              beta=float(lattice["beta"]), gamma=float(lattice["gamma"]))

                        SetUB(ws_norm, a=float(lattice["a"]), b=float(lattice["b"]), c=float(lattice["c"]),
                              u=scatter["u"], v=scatter["v"], alpha=float(lattice["alpha"]),
                              beta=float(lattice["beta"]), gamma=float(lattice["gamma"]))

                        SetGoniometer(ws, Axis0="omega, 0, 1, 0, 1")
                        AddSampleLog(ws, LogName="Omega0", LogType="Number", LogUnit="Degrees",
                                     LogText=str(float(omega)-self.sampleParameters["Omega offset"]))
                        SetGoniometer(ws, Axis0="Omega0, 0, 1, 0, -1")

                        SetGoniometer(ws_norm, Axis0="omega, 0, 1, 0, 1")
                        AddSampleLog(ws_norm, LogName="Omega0", LogType="Number", LogUnit="Degrees",
                                     LogText=str(float(omega)-self.sampleParameters["Omega offset"]))
                        SetGoniometer(ws_norm, Axis0="Omega0, 0, 1, 0, -1")

                        ConvertToDiffractionMDWorkspace(ws, Append=True, OneEventPerBin=False, OutputDimensions="HKL",
                                                        Extents="-2.5,2.5", SplitInto="100", LorentzCorrection=False,
                                                        OutputWorkspace=result_name)

                        ConvertToDiffractionMDWorkspace(ws_norm, Append=True, OneEventPerBin=False,
                                                        OutputDimensions="HKL", Extents="-2.5,2.5", SplitInto="100",
                                                        LorentzCorrection=False, OutputWorkspace=result_name_norm)

                result_name_end = self.out_ws_name+"_sc_"+pol+flip+"_proj_res"

                result_ws   = mtd[result_name]

                nopix = not self.keep_events

                # convert event multi dimensional workspace to histogram multi dimensional workspace to
                # divide workspace by norm workspace

                result_name_proj = self.out_ws_name+"_sc_"+pol+flip+"_proj"
                result_ws        = CutMD(result_ws, Projection=proj_ws, PBins=([0.01], [0.01], [-2.5, 2.5]),
                                         NoPix=nopix, OutputWorkspace=result_name_proj)

                result_dim0 = result_ws.getDimension(0)
                result_dim1 = result_ws.getDimension(1)
                result_dim2 = result_ws.getDimension(2)
                result_hist = BinMD(result_ws,
                                    AlignedDim0="{}, {}, {}, {}".format(result_dim0.getDimensionId(),
                                                                        result_dim0.getMinimum(),
                                                                        result_dim0.getMaximum(),
                                                                        result_dim0.getNBins()),
                                    AlignedDim1="{}, {}, {}, {}".format(result_dim1.getDimensionId(),
                                                                        result_dim1.getMinimum(),
                                                                        result_dim1.getMaximum(),
                                                                        result_dim1.getNBins()),
                                    AlignedDim2="{}, {}, {}, {}".format(result_dim2.getDimensionId(),
                                                                        result_dim2.getMinimum(),
                                                                        result_dim2.getMaximum(),
                                                                        result_dim2.getNBins()),
                                    OutputWorkspace=result_name+"_histo")
                result_ws_norm   = mtd[result_name_norm]

                result_name_proj_norm = self.out_ws_name+"_sc_"+pol+flip+"_proj_norm"
                result_ws_norm        = CutMD(result_ws_norm, Projection=proj_ws, PBins=([0.01], [0.01], [-2.5, 2.5]),
                                              NoPix=nopix, OutputWorkspace=result_name_proj_norm)

                result_dim0_norm = result_ws_norm.getDimension(0)
                result_dim1_norm = result_ws_norm.getDimension(1)
                result_dim2_norm = result_ws_norm.getDimension(2)
                result_hist_norm = BinMD(result_ws_norm,
                                         AlignedDim0="{}, {}, {}, {}".format(result_dim0_norm.getDimensionId(),
                                                                             result_dim0_norm.getMinimum(),
                                                                             result_dim0_norm.getMaximum(),
                                                                             result_dim0_norm.getNBins()),
                                         AlignedDim1="{}, {}, {}, {}".format(result_dim1_norm.getDimensionId(),
                                                                             result_dim1_norm.getMinimum(),
                                                                             result_dim1_norm.getMaximum(),
                                                                             result_dim1_norm.getNBins()),
                                         AlignedDim2="{}, {}, {}, {}".format(result_dim2_norm.getDimensionId(),
                                                                             result_dim2_norm.getMinimum(),
                                                                             result_dim2_norm.getMaximum(),
                                                                             result_dim2_norm.getNBins()),
                                         OutputWorkspace=result_name_norm+"_histo")

                result_ws_end = DivideMD(result_hist, result_hist_norm, OutputWorkspace=result_name_end)

                result_ws_end.setComment(self.comment)

                end_group.append(result_ws_end)

                ConvertMDHistoToMatrixWorkspace(result_ws_end, OutputWorkspace=result_ws_end.getName()+"_2D")

                # save multi dimensional result workspace to file
                self._save_md_to_file(flip, pol)

                if self.keep_events:
                    sv = mantidplot.plotSlice(result_name_end, normalization=0, colormin=0.01, colormax=1000.0,
                                              colorscalelog=True, limits=[-0.2, 1.4, -3.0, 5.0])
                    sv.setTransparentZeros(True)
                if not self.keep_events:
                    SmoothMD(result_name_proj, 3, "Gaussian",
                             OutputWorkspace=self.out_ws_name+"_sc_"+pol+flip+"_smooth")

        GroupWorkspaces(end_group, OutputWorkspace=self.out_ws_name)

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty("SampleTable",              defaultValue="", doc="Name of the sample data ITableWorkspace")
        self.declareProperty("SubtractBackground",       defaultValue="", doc="Bool if subtract background for sample")
        self.declareProperty("SubtractBackgroundFactor", defaultValue="", doc="Factor for background subtraction")
        self.declareProperty("DeteEffiCorrection",       defaultValue="", doc="Bool if correct detector efficiency")
        self.declareProperty("FlipRatioCorrection",      defaultValue="", doc="Bool if correct flipping ratio")
        self.declareProperty("SampleParameters",         defaultValue="", doc="Dictionary of the sample parameters")
        self.declareProperty("OutputWorkspace",          defaultValue="", doc="Name of the output workspace")
        self.declareProperty("OutputXAxis",              defaultValue="", doc="List of the output x axis units")
        self.declareProperty("Comment",                  defaultValue="", doc="Comment for the output workspace")
        self.declareProperty("Omegas",                   defaultValue="", doc="List of omegas")
        self.declareProperty("OutputFileDirectory",      defaultValue="", doc="Directory to save files")
        self.declareProperty("OutputFilePrefix",         defaultValue="", doc="Prefix of the files to save")

    def PyExec(self):

        sample_table = mtd[self.getProperty("SampleTable").value]

        subInst = self.getProperty("SubtractBackground").value
        subInst = eval(subInst)
        if subInst:
            subInstFac = float(self.getProperty("SubtractBackgroundFactor").value)
        else:
            subInstFac = ""

        detEffi = self.getProperty("DeteEffiCorrection").value
        detEffi = eval(detEffi)

        flipRatio = self.getProperty("FlipRatioCorrection").value
        flipRatio = eval(flipRatio)

        parameters = self.getProperty("SampleParameters").value
        self.sampleParameters = eval(parameters)

        self.out_ws_name = self.getProperty("OutputWorkspace").value
        self.xax         = self.getProperty("OutputXAxis").value
        self.comment     = self.getProperty("Comment").value

        omegas = self.getProperty("Omegas").value.split(", ")

        self.out_file_prefix    = self.getProperty("OutputFilePrefix").value
        self.out_file_directory = self.getProperty("OutputFileDirectory").value

        tmp = LoadEmptyInstrument(InstrumentName="DNS")
        instrument = tmp.getInstrument()
        DeleteWorkspace(tmp)

        self.suff_norm  = instrument.getStringParameter("normws_suffix")[0]
        self.keep_events = instrument.getBoolParameter("keep_events")[0]
        self._m_and_n   = instrument.getBoolParameter("keep_intermediate_workspace")[0]

        if self.sampleParameters["Type"] == "Single Crystal":
            self.sc = True
        else:
            self.sc = False

        self._get_end_name(detEffi, flipRatio)

        self.omegas_data   = []
        self.polarisations = []

        # workspace to rebin to
        self.rebin_ws_name = self.out_ws_name+"_data_"+sample_table.cell("polarisation", 0)+"_sf"+self.end_name+"_m_"

        self._do_correction(sample_table, detEffi, flipRatio, subInst, subInstFac, omegas)

        if self.sampleParameters["Type"] == "Polycrystal/Amorphous":
            if self.sampleParameters["Separation"] == "XYZ":
                self._xyz_separation()
            elif self.sampleParameters["Separation"] == "No":
                self._no_separation()

        if self.sampleParameters["Type"] == "Single Crystal":
            self._single_crystal_correction()

        # save end workspaces to files
        if self.out_file_directory and not self.sc:
            for pol in self.polarisations:
                self._save_to_file("_data_"+pol+"_sf"+self.end_name+"_m_", flip="_sf", pol="_"+pol)
                self._save_to_file("_data_"+pol+"_nsf"+self.end_name+"_m_", flip="_nsf", pol="_"+pol)

        print('out file dir: ', type(self.out_file_directory))
        print('bkg group: ', type(self.bkg_group_sf))
        print('bkg group: ', type(self.bkg_group_nsf))
        print('comment: ', type(self.comment))
        print('data groups: ', type(self.data_group_sf))
        print('data groups: ', type(self.data_group_nsf))
        print('data norm: ', type(self.data_sf_norm))
        print('data norm: ', type(self.data_nsf_norm))
        print('data fcorr: ', type(self.data_sf_fcorr))
        print('data fcorr: ', type(self.data_nsf_fcorr))
        print('keep events: ', type(self.keep_events))
        print('nicr coef normalized: ', type(self.nicr_coef_normalized))
        print('omegas_data: ', type(self.omegas_data))
        print('polarisations: ', type(self.polarisations))
        print('vana coefs total: ', type(self.vana_coefs_total))


AlgorithmFactory.subscribe(DNSProcessSampleData)
