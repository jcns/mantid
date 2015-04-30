from mantid.kernel import *
from mantid.api import *
import mantid.simpleapi as api
import numpy as np
import os, sys


NORMALIZATIONS = ['duration', 'mon_sum']


class DetectorEfficiencyCorVana(PythonAlgorithm):
    """
    Peforms detector efficiency correction on a given data workspace
    using the Vanadium data.
    This algorithm is written for the DNS @ MLZ,
    but can be used for other instruments if needed.
    """
    def category(self):
        """
        Returns categore
        """
        return 'CorrectionFunctions\\EfficiencyCorrections'

    def name(self):
        """
        Returns name
        """
        return "DetectorEfficiencyCorVana"

    def summary(self):
        return " Peforms detector efficiency correction \
                on a given data workspace using the Vanadium data."

    def PyInit(self):
        self.declareProperty(WorkspaceProperty("InputWorkspace",
                "", direction=Direction.Input), \
                doc="A workspace with raw experimental data.")
        self.declareProperty(WorkspaceProperty("OutputWorkspace", \
                "", direction=Direction.Output), \
                doc="A workspace to save the corrected data.")
        self.declareProperty(WorkspaceProperty("VanaWorkspace", \
                "", direction=Direction.Input), \
                doc="A workspace with Vanadium data.")
        self.declareProperty(WorkspaceProperty("BkgWorkspace", \
                "", direction=Direction.Input), \
                doc="A workspace with Vanadium background.")
        self.declareProperty("NormalizeTo", "Duration", \
                StringListValidator(NORMALIZATIONS), \
                doc="Type of normalization for Vanadium and Background. \
                Valid values: %s" % str(NORMALIZATIONS))
        return


    def PyExec(self):
        # [TODO:] check whether input workspace is one of the "created"
        # to avoid the infinite recursion
        # Input
        dataws = mtd[self.getPropertyValue("InputWorkspace")]
        outws = self.getPropertyValue("OutputWorkspace")
        vanaws = mtd[self.getPropertyValue("VanaWorkspace")]
        bkgws = mtd[self.getPropertyValue("BkgWorkspace")]
        norm = self.getPropertyValue("NormalizeTo")
        # all given workspaces must have the same number of dimensions
        # and the same number of histograms
        nd = dataws.getNumDims()
        nh = dataws.getNumberHistograms()
        if (vanaws.getNumDims() != nd or vanaws.getNumberHistograms() != nh):
            raise ValueError("The dimensions of Vanadium workspace are not valid.")
        if (bkgws.getNumDims() != nd or bkgws.getNumberHistograms() != nh):
            raise ValueError("The dimensions of Background workspace are not valid.")
        bkg_run = bkgws.getRun()
        vana_run = vanaws.getRun()
        # [TODO:] check slits, produce warning if different
        # [TODO:] check deterota, complain if it is out of tolerance range
        # 1. normalize Vanadium and Background
        try:
            bkg_nvalue = bkg_run.getProperty(norm).value
            vana_nvalue = vana_run.getProperty(norm).value
        except:
            raise ValueError("The normalization parameter %s is not valid" % norm)
        else:
            # numpy.full is not supported by 'mantid' numpy!
            # dataY = np.full((nd-1, nh), nvalue)
            dataY = np.empty((nd-1, nh))
            dataY.fill(bkg_nvalue)
            dataX = np.zeros(nh)
            dataE = np.zeros((nd-1, nh)) # the monitor error is neglected
            bkg_normws = api.CreateWorkspace(DataX=dataX, \
                DataY=dataY, DataE=dataE, NSpec=nh, UnitX="Wavelength")
            dataY.fill(vana_nvalue)
            vana_normws = api.CreateWorkspace(DataX=dataX, \
                DataY=dataY, DataE=dataE, NSpec=nh, UnitX="Wavelength")
            vana_norm = api.Divide(vanaws, vana_normws)
            bkg_norm = api.Divide(bkgws, bkg_normws)
            # 2. substract background from Vanadium
            vana_bg = vana_norm - bkg_norm
            # [TODO:] check negative values, complain laud
            # 3. calculate correction coefficients
            # [TODO:] Make IncludeMonitors to external parameter
            vana_mean_ws = api.SumSpectra(vana_bg, IncludeMonitors=True) / nh
            coef_ws = api.Divide(vana_bg, vana_mean_ws)
            # 4. correct raw data (not normalized!)
            __corrected_data__ = api.Divide(dataws, coef_ws)

            self.setProperty("OutputWorkspace", __corrected_data__)
            self.log().debug('DetectorEfficiencyCorVana: OK')
            api.DeleteWorkspace(__corrected_data__)

        return

# Register algorithm with Mantid
AlgorithmFactory.subscribe(DetectorEfficiencyCorVana)
