from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import numpy as np
from scipy.integrate import quad
import scipy as sp
import re

# Test for keyword Vanadium or vanadium in Title - compulsory entries
class CalibrateDetectorSensitivities(PythonAlgorithm):
    """ Calculate coefficient to normalize by Vanadium and correct Debye Waller
    """
    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;Utilities"
    def name(self):
        """ Return summary
        """
        return "CalibrateDetectorSensitivities"

    def summary(self):
        return "Calculate coefficient to normalize by Vanadium and correct Debye Waller"

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty(WorkspaceProperty("InputWorkspace","",direction=Direction.Input), "Input Vanadium workspace")
        self.declareProperty(WorkspaceProperty("OutputWorkspace","", direction=Direction.Output), "Name the workspace that will contain the result")
        return

    def PyExec(self):
        """ Main execution body
        """
        self._wksp = self.getProperty("InputWorkspace").value
        self._owksp = self.getProperty("OutputWorkspace").value

        run=self._wksp.getRun()

        # Check if inputworkspace is from Vanadium data
        if not re.search(r"(?i)(vanadium)", str(run.getLogData('run_title').value)):
            raise ValueError( 'Wrong workspace type for data file')

        nb_block=self._wksp.blocksize()
        nb_hist = self._wksp.getNumberHistograms()
        self._owksp = self._wksp+0.

        # See Sears and Shelley Acta Cryst. A 47, 441 (1991)
        DWF=np.zeros(nb_hist) #Debye Waller factor corection. One value per spectrum or detector
        thetasort=np.zeros(nb_hist) #theta in radians !!!NOT 2Theta
        for i in range(nb_hist):
            det = self._wksp.getInstrument().getDetector(i)
            r = np.sqrt((det.getPos().X())**2+\
                        (det.getPos().Y())**2+\
                        (det.getPos().Z())**2)
            thetasort[i]= np.sign(det.getPos().X())*np.arccos(det.getPos().Z()/r)/2.


        Tempk=float(run.getLogData('temperature').value)
        wlength = float(run.getLogData('wavelength').value) #in angstroem
        Tm=389. # from Sears paper
        MVana=50.942/1000./sp.constants.N_A # Vanadium atomic mass
        if (Tempk < 1.e-3*Tm):
            integral = 0.5
        else:
            y=Tempk/Tm
        def integrand(x,y):
            return x/sp.tanh(x/2./y)
        integral = quad(integrand,0,1,args=(y))[0]
        u2=3.*sp.constants.hbar**2/(2.*MVana*sp.constants.k *Tm)*integral*1.e20
        DWF=np.exp(-u2*(4.*sp.pi/wlength*sp.sin(thetasort))**2)

        array_count_vanadium=np.zeros(nb_block)
        array_error_vanadium=np.zeros(nb_block)
        for i in range(nb_hist):
            #crop around max EPP + fit to get fwhm
            array=self._wksp.readY(i)
            arrayx=self._wksp.readX(i)
            arrayerr=self._wksp.readE(i)
            if np.max(array) !=0:
                #First guess for fitting parameters
                tryCentre = arrayx[np.argmax(array)]
                height = np.max(array)# start guess on peak height
                inx = np.argwhere(array>0.5*height)
                sigma = (arrayx[inx[len(inx)-1][0]]-arrayx[inx[0][0]])/2.*np.sqrt(2.*np.log(2.)) # start guess on peak width
                #Fitting windows
                startx = tryCentre-10.*sigma
                endx = tryCentre+10.*sigma
                myFunc = 'name=Gaussian, Height='+str(height)+', PeakCentre='+str(tryCentre)+', Sigma='+str(sigma) 
                #Run fitting
                fitStatus, chiSq, covarianceTable, paramTable, fitWorkspace = Fit(InputWorkspace=self._wksp, \
                WorkspaceIndex=i, StartX = startx, EndX=endx, Output='fitVanadium', Function=myFunc, MaxIterations=100)
                #Definition of fwhm to crop vanadium counts and sum
                fwhm= 2.*np.sqrt(2.*np.log(2.))*paramTable.column(1)[2]
                peakCentre = paramTable.column(1)[1]
                #print fwhm, peakCentre, height
                idxmin = (np.abs(arrayx-peakCentre+3.*fwhm)).argmin()
                idxmax = (np.abs(arrayx-peakCentre-3.*fwhm)).argmin()
                array_count_vanadium[:]=DWF[i]/(float(idxmax)-float(idxmin)+1.)*sum(array[j] for j in range(idxmin,idxmax+1))
                array_error_vanadium[:]=np.sqrt(DWF[i])*sum(arrayerr[j] for j in range(idxmin,idxmax+1))
            else:
                array_count_vanadium[:]=0.
                array_error_vanadium[:]=0.
            #Fill output workspace
            self._owksp.setX(i,arrayx)
            self._owksp.setY(i,array_count_vanadium)
            self._owksp.setE(i,array_error_vanadium)
           

        self.setProperty("OutputWorkspace",self._owksp)      
    
#########################################################################################
# Registration
AlgorithmFactory.subscribe(CalibrateDetectorSensitivities)
