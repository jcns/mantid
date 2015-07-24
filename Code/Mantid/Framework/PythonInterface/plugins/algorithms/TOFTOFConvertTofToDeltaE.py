#pylint: disable=no-init
from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import numpy as np
import scipy as sp


# Test for keyword Vanadium or vanadium in Title - compulsory entries
class TOFTOFConvertTofToDeltaE(PythonAlgorithm):
    """ Calculate energy transfer using elastic tof
    """
    _wksp = None
    _owksp = None
    _wkspvana = None

    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;Transforms\\Units;CorrectionFunctions"

    def name(self):
        """ Return summary
        """
        return "TOFTOFConvertTofToDeltaE"

    def summary(self):
        return "Calculates the energy transfer using elastic tof with three options to calculate it: " \
               "geometry (guess - default), fit from vanadium or fit from sample."

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty(WorkspaceProperty("InputWorkspace", "", direction=Direction.Input),
                             "Input Sample workspace")
        # Optional but required if choice of tof_elastic from Vanadium ws or file
        self.declareProperty(MatrixWorkspaceProperty("WorkspaceVanadium", "", direction=Direction.Input,
                                                     optional=PropertyMode.Optional),
                             "Input Vanadium workspace (optional)")
        self.declareProperty(WorkspaceProperty("OutputWorkspace", "", direction=Direction.Output),
                             "Name the workspace that will contain the result")
        choice_tof = ["Geometry", "FitVanadium", "FitSample"]
        self.declareProperty("ChoiceElasticTof", "Geometry", StringListValidator(choice_tof))
        return

    def _FitGaussian(self, wstofit):
        nb_hist = wstofit.getNumberHistograms()
        TableFit = np.zeros(nb_hist)
        for i in range(nb_hist):
            # prog_reporter.report("Setting fit for %dth spectrum" % (i))
            x_values = wstofit.readX(i)
            y_values = wstofit.readY(i)
            if np.max(y_values) != 0:
                imax = np.argmax(y_values)
                ymax = y_values[imax]
                tryCentre = x_values[imax]
                height = ymax  # start guess on peak height
                inx = np.argwhere(y_values > 0.5 * height)
                sigma = (x_values[inx[len(inx) - 1][0]] - x_values[inx[0][0]]) / (
                    2. * np.sqrt(2. * np.log(2.)))  # start guess on peak width
                fitAlg = self.createChildAlgorithm('Fit')
                fitAlg.setProperty('Function', 'name=Gaussian, Height=' + str(height) + ', PeakCentre=' + str(tryCentre)
                                   + ', Sigma=' + str(sigma))
                fitAlg.setProperty('InputWorkspace', wstofit)
                fitAlg.setProperty('WorkspaceIndex', i)
                fitAlg.setProperty('StartX', tryCentre - 10. * sigma)
                fitAlg.setProperty('EndX', tryCentre + 10. * sigma)
                fitAlg.setProperty('Output', 'fitGaussianTof2dE')
                fitAlg.setProperty('CreateOutput', True)
                fitAlg.execute()
                paramTable = fitAlg.getProperty('OutputParameters').value
                TableFit[i] = paramTable.column(1)[1]
            else:
                TableFit[i] = 0.
        return TableFit

    def PyExec(self):
        """ Main execution body
        """
        self._wksp = self.getProperty("InputWorkspace").value
        #Outputws = self.getProperty("OutputWorkspace").value

        # check TOFTOF
        if self._wksp.getInstrument().getName() != 'TOFTOF':
            raise ValueError('Wrong instrument')

        run = self._wksp.getRun()
        choice_tof = self.getProperty("ChoiceElasticTof").value

        nb_block = self._wksp.blocksize()
        nb_hist = self._wksp.getNumberHistograms()

        prog_reporter = Progress(self, start=0.0, end=1.0, nreports=nb_hist + 1)  # extra call below when summing

        if choice_tof == 'Geometry':
            # tof_elastic from header of raw datafile
            tof_elastic = np.zeros(nb_hist)
            # start guess on peak width
            tof_elastic[:] = float(run.getLogData('EPP').value) * float(run.getLogData('channel_width').value)

        if choice_tof == 'FitSample':
            prog_reporter.report("Fit function")
            tof_elastic = self._FitGaussian(self._wksp)
        if choice_tof == 'FitVanadium':
            self._wkspvana = self.getProperty("WorkspaceVanadium").value
            prog_reporter.report("Fit function")
            tof_elastic = self._FitGaussian(self._wkspvana)

        sample = self._wksp.getInstrument().getSample()
        # samplePos = sample.getPos()
        # sourcePos = self._wksp.getInstrument().getSource().getPos()
        Lsd = self._wksp.getInstrument().getDetector(1).getDistance(sample)
        Outputws = self._wksp + 0.
        arrayx = np.zeros(nb_block + 1)  # will be filled for each histogram

        # dx = sp.array([self._wksp.readX(1)[i]-self._wksp.readX(1)[i-1] for i in range(1,len(arrayx))])
        deltax = sp.array([self._wksp.readX(1)[i + 1] - self._wksp.readX(1)[i] for i in range(len(arrayx) - 1)])
        arrayynorm = sp.array([(self._wksp.readX(1)[i]) ** 3 / (deltax[i]) for i in range(nb_block)])
        # arrayynorm=sp.array([(self._wksp.readX(1)[i])**3 for i in range(nb_block)])

        arrayynorm *= sp.constants.eV / (1.e15 * sp.constants.m_n * Lsd ** 2)
        for j in range(nb_hist):
            prog_reporter.report("Setting %dth spectrum" % i)
            if tof_elastic[j] != 0.:
                for i in range(nb_block + 1):
                    arrayx[i] = (-1. / self._wksp.readX(j)[i] ** 2 + 1. / tof_elastic[j] ** 2)
                    # if i ==0:
                    #    self.log().debug("DeltaE, t: %s, %s"%(arrayx[i],self._wksp.readX(j)[i]))
                    # arrayx[i]=0.5*sp.constants.m_n*Lsd**2*(-1./self._wksp.readX(j)[i]**2+1./tof_elastic[j]**2)*10.**15/sp.constants.eV
            Outputws.setX(j, 0.5 * sp.constants.m_n * Lsd ** 2 * 10. ** 15 / sp.constants.eV * arrayx)
            newy = arrayynorm * Outputws.readY(j)
            newe = arrayynorm * Outputws.readE(j)
            Outputws.setY(j, newy)
            Outputws.setE(j, newe)

        Outputws.getAxis(0).setUnit('DeltaE')

        self.setProperty("OutputWorkspace", Outputws)

# Register algorithm with Mantid.
AlgorithmFactory.subscribe(TOFTOFConvertTofToDeltaE)
