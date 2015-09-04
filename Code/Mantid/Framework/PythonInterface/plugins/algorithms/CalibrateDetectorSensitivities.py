#pylint: disable=no-init
from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import numpy as np
from scipy import integrate
import scipy as sp
import re


# Test for keyword Vanadium or vanadium in Title - compulsory entries
class CalibrateDetectorSensitivities(PythonAlgorithm):
    """ Calculate coefficient to normalize by Vanadium and correct Debye Waller factor
    """
    _wksp = None

    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;CorrectionFunctions\\EfficiencyCorrections"

    def name(self):
        """ Return summary
        """
        return "CalibrateDetectorSensitivities"

    def summary(self):
        return "Calculate coefficient to normalize by Vanadium and correct Debye Waller factor"

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty(WorkspaceProperty("InputWorkspace", "", direction=Direction.Input),
                             "Input Vanadium workspace")
        self.declareProperty(WorkspaceProperty("OutputWorkspace", "", direction=Direction.Output),
                             "Name the workspace that will contain the result")
        return

    def PyExec(self):
        """ Main execution body
        """
        self._wksp = self.getProperty("InputWorkspace").value

        # Check if inputworkspace is from Vanadium data
        # if not re.search(r"(?i)(vanadium)", str(self._wksp.getRun().getLogData('run_title').value)):
        #    raise ValueError('Wrong workspace type for data file')

        wsOutput = self._FillOutputWorkspace(self._wksp)
        self.setProperty("OutputWorkspace", wsOutput)
        # DeleteWorkspace(wsOutput)

    def _FitGaussian(self, wstofit):
        nb_hist = wstofit.getNumberHistograms()
        TableFit = np.zeros((nb_hist, 2))
        for i in range(nb_hist):
            x_values = wstofit.readX(i)
            y_values = wstofit.readY(i)
            if np.max(y_values) != 0:
                imax = np.argmax(y_values)
                ymax = y_values[imax]
                tryCentre = x_values[imax]
                # start guess on peak width
                height = ymax
                inx = np.argwhere(y_values>0.5*height)
                # fwhm = x_values[inx[len(inx)-1][0]]-x_values[inx[0][0]]
                #####
                # start guess on peak width
                sigma = (x_values[inx[len(inx)-1][0]]-x_values[inx[0][0]])/(2.*np.sqrt(2.*np.log(2.)))
                fitAlg = self.createChildAlgorithm('Fit')
                fitAlg.setProperty('Function', 'name=Gaussian, Height=' + str(height) + ', PeakCentre=' + str(tryCentre)
                                   + ', Sigma='+str(sigma))
                fitAlg.setProperty('InputWorkspace', wstofit)
                fitAlg.setProperty('WorkspaceIndex', i)
                fitAlg.setProperty('StartX', tryCentre-5.*sigma)
                fitAlg.setProperty('EndX', tryCentre+5.*sigma)
                fitAlg.setProperty('CreateOutput', True)
                fitAlg.execute()
                paramTable = fitAlg.getProperty('OutputParameters').value
                TableFit[i, 0] = paramTable.column(1)[1]
                TableFit[i, 1] = paramTable.column(1)[2]
            else:
                TableFit[i, :] = 0.
        return TableFit

    def _CalculateDebyeWallerCorrection(self, wsToCorrect):
        # See Sears and Shelley Acta Cryst. A 47, 441 (1991)
        run = wsToCorrect.getRun()
        nb_hist_ws = wsToCorrect.getNumberHistograms()
        thetasort = np.zeros(nb_hist_ws)  # theta in radians !!!NOT 2Theta

        for i in range(nb_hist_ws):
            det = wsToCorrect.getInstrument().getDetector(i)
            radial_pos = np.sqrt((det.getPos().X())**2 + (det.getPos().Y())**2 + (det.getPos().Z())**2)
            thetasort[i] = np.sign(det.getPos().X())*np.arccos(det.getPos().Z()/radial_pos)/2.

        if not 'temperature' in run.keys() or not str(run.getLogData('temperature').value):
            Tempk = 293.  # in K. assumes room temperature if not defined in input file
            logger.warning("No temperature was given. T= %f K is assumed for the Debye Waller factor." % Tempk)
            print "No temperature was given. T= ", Tempk, " K is assumed for the Debye Waller factor."
        else:
            Tempk = float(run.getLogData('temperature').value)
        # Wavelength in AA
        wlength = float(run.getLogData('wavelength').value)
        # Temperature in K. from Sears paper
        Tempm = 389.
        # start guess on peak width
        MVana = 50.942/1000./sp.constants.N_A
        if Tempk < 1.e-3*Tempm:
            integral = 0.5
        else:
            Temp_ratio = Tempk/Tempm
            def integrand(var1, var2):
                return var1/sp.tanh(var1/2./var2)
            integral = integrate.quad(integrand, 0, 1, args=Temp_ratio)[0]
        msd = 3.*sp.constants.hbar**2/(2.*MVana*sp.constants.k * Tempm)*integral*1.e20
        return np.exp(-msd*(4.*sp.pi/wlength*sp.sin(thetasort))**2)

    def _FillOutputWorkspace(self, wsInput):
        nb_hist = wsInput.getNumberHistograms()
        prog_reporter = Progress(self, start=0.0, end=1.0, nreports=nb_hist+1)
        nb_block = wsInput.blocksize()
        array_count_vanadium = np.zeros(nb_block)
        array_error_vanadium = np.zeros(nb_block)
        arrayx = wsInput.readX(0)

        #wsOutput = wsInput +0. #CloneWorkspace(wsInput)
        DWF = self._CalculateDebyeWallerCorrection(wsInput)
        FittingParam = self._FitGaussian(wsInput)

        for i in range(nb_hist):
            # crop around max EPP + fit to get fwhm
            prog_reporter.report("Setting %dth spectrum" % i)
            array = wsInput.readY(i)
            if np.max(array) != 0:
                arrayerr = wsInput.readE(i)
                fwhm = FittingParam[i, 1]  # 2.*np.sqrt(2.*np.log(2.))*Table[i,1]
                peakCentre = FittingParam[i, 0]
                idxmin = (np.abs(arrayx-peakCentre+3.*fwhm)).argmin()
                idxmax = (np.abs(arrayx-peakCentre-3.*fwhm)).argmin()
                elt_county_vanadium = DWF[i]*sum(array[j] for j in range(idxmin, idxmax+1))
                elt_counte_vanadium = DWF[i]*sum(arrayerr[j] for j in range(idxmin, idxmax+1))
            else:
                elt_county_vanadium = 0.
                elt_counte_vanadium = 0.
            array_count_vanadium[:] = elt_county_vanadium
            array_error_vanadium[:] = elt_counte_vanadium
            # Fill output workspace
            wsInput.setY(i, array_count_vanadium)
            wsInput.setE(i, array_error_vanadium)
        return wsInput

# Register algorithm with Mantid.
AlgorithmFactory.subscribe(CalibrateDetectorSensitivities)
