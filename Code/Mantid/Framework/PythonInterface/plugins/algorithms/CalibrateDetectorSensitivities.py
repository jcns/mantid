from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import numpy as np
from scipy.integrate import quad
import scipy as sp
import re

# Test for keyword Vanadium or vanadium in Title - compulsory entries
class CalibrateDetectorSensitivities(PythonAlgorithm):
    """ Normalize by Vanadium and correct Debye Waller
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
        return "Normalize by Vanadium and correct Debye Waller"

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
        #print str(run.getLogData('run_title').value)

        if not re.search(r"(?i)(vanadium)", str(run.getLogData('run_title').value)):
            raise ValueError( 'Wrong workspace type for data file')

        nb_block=self._wksp.blocksize()
        nb_hist = self._wksp.getNumberHistograms()

        #self._owksp = WorkspaceFactory.create("Workspace2D", NVectors=nb_hist, 
        #         XLength=nb_block+1, YLength=nb_block)
        self._owksp = self._wksp+0.

        DWF=np.zeros(nb_hist) #input workspace
        thetasort=np.zeros(nb_hist) #theta in radians
        for i in range(nb_hist):
            det = self._wksp.getInstrument().getDetector(i+1)
            r = np.sqrt((det.getPos().X())**2+\
                        (det.getPos().Y())**2+\
                        (det.getPos().Z())**2)
            thetasort[i]= np.sign(det.getPos().X())*np.arccos(det.getPos().Z()/r)/2.

        Tempk=float(run.getLogData('temperature').value)
        wlength = float(run.getLogData('wavelength').value)
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
            print i
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
                ##min(range(len(array)), key=lambda i: abs(array[i]-startx))[1]
                #min(enumerate(array), key=lambda x: abs(x[1]-startx))[1]
                #min(enumerate(array), key=lambda x: abs(x[1]-endx))[1]
                #backgd = 0.5*(min(enumerate(array), key=lambda x: abs(x[1]-startx))[1]+min(enumerate(array), key=lambda x: abs(x[1]-endx))[1])
                # Function to fit
                #myFunc = 'name=LinearBackground, A0='+str(backgd)+ ';name=Gaussian, Height='+str(height)+', PeakCentre='+str(tryCentre)+', Sigma='+str(sigma)
                myFunc = 'name=Gaussian, Height='+str(height)+', PeakCentre='+str(tryCentre)+', Sigma='+str(sigma) 
                #Run fitting
                fitStatus, chiSq, covarianceTable, paramTable, fitWorkspace = Fit(InputWorkspace=self._wksp, \
                WorkspaceIndex=i, StartX = startx, EndX=endx, Output='fitVanadium', Function=myFunc, MaxIterations=100)
                #Definition of fwhm to crop vanadium counts and sum
                fwhm= 2.*np.sqrt(2.*np.log(2.))*paramTable.column(1)[2]
                idxmin = (np.abs(arrayx-paramTable.column(1)[1]+3.*fwhm)).argmin()
                idxmax = (np.abs(arrayx-paramTable.column(1)[1]-3.*fwhm)).argmin()
                array_count_vanadium[:]=DWF[i]*sum(array[i] for i in range(idxmin,idxmax+1))
                array_error_vanadium[:]=np.sqrt(DWF[i])*sum(arrayerr[i] for i in range(idxmin,idxmax+1))
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
