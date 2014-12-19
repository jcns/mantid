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
        return "PythonAlgorithms;MLZ"
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
    
    def _FitGaussiang(self,ws):
        nb_hist = ws.getNumberHistograms()
        TableFit=np.zeros((nb_hist, 2))#4))
        for i in range(nb_hist):
            x_values = ws.readX(i)
            y_values = ws.readY(i)
            if np.max(y_values) !=0:
                imax=np.argmax(y_values)
                ymax=y_values[imax]
                tryCentre = x_values[imax]
                height = ymax# start guess on peak height
                inx = np.argwhere(y_values>0.5*height)
                sigma = x_values[inx[len(inx)-1][0]]-x_values[inx[0][0]] # start guess on peak width
                fitAlg = self.createChildAlgorithm('Fit')
                fitAlg.setProperty('Function','name=Gaussian, Height='+str(height)+', PeakCentre='+str(tryCentre)+', Sigma='+str(sigma))
                fitAlg.setProperty('InputWorkspace', ws)
                fitAlg.setProperty('WorkspaceIndex', i)
                fitAlg.setProperty('StartX', tryCentre-sigma)
                fitAlg.setProperty('EndX', tryCentre+sigma)
                fitAlg.setProperty('MaxIterations',10)
                fitAlg.setProperty('CreateOutput',True)
                fitAlg.execute()
                paramTable = fitAlg.getProperty('OutputParameters').value
                TableFit[i,0]=paramTable.column(1)[1]
                TableFit[i,1]=paramTable.column(1)[2]
                #TableFit[i,2]=paramTable.column(2)[1]
                #TableFit[i,3]=paramTable.column(2)[2]               
            else:
                TableFit[i,:]=0.
        return TableFit
    
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

        # See Sears and Shelley Acta Cryst. A 47, 441 (1991)
        DWF=np.zeros(nb_hist) #Debye Waller factor corection. One value per spectrum or detector
        thetasort=np.zeros(nb_hist) #theta in radians !!!NOT 2Theta
        for i in range(nb_hist):
            det = self._wksp.getInstrument().getDetector(i)
            r = np.sqrt((det.getPos().X())**2+\
                        (det.getPos().Y())**2+\
                        (det.getPos().Z())**2)
            thetasort[i]= np.sign(det.getPos().X())*np.arccos(det.getPos().Z()/r)/2.
            
        if not 'temperature' in run.keys() or not str(run.getLogData('temperature').value):
            Tempk=293. # in K. assumes room temperature if not defined in input file
            logger.warning("No temperature was given. T= %f K is assumed for the Debye Waller factor." % Tempk)
            print "No temperature was given. T= ",Tempk," K is assumed for the Debye Waller factor."
        else:
            Tempk=float(run.getLogData('temperature').value)
    
        wlength = float(run.getLogData('wavelength').value) #in AA
        Tm = 389. # in K. from Sears paper
        MVana = 50.942/1000./sp.constants.N_A # Vanadium atomic mass
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
        arrayx=self._wksp.readX(0)
        
        self._owksp = self._wksp+0.
        
        Table=self._FitGaussiang(self._wksp)
        
        for i in range(nb_hist):
            #crop around max EPP + fit to get fwhm
            array=self._wksp.readY(i)
            if np.max(array) !=0:
                arrayerr=self._wksp.readE(i)
                fwhm= 2.*np.sqrt(2.*np.log(2.))*Table[i,1]
                peakCentre = Table[i,0]
                idxmin = (np.abs(arrayx-peakCentre+3.*fwhm)).argmin()
                idxmax = (np.abs(arrayx-peakCentre-3.*fwhm)).argmin()
                
                elt_county_vanadium=DWF[i]*sum(array[j] for j in range(idxmin,idxmax+1))
                elt_counte_vanadium=DWF[i]*sum(arrayerr[j] for j in range(idxmin,idxmax+1))
            else:
                elt_county_vanadium=0.
                elt_counte_vanadium=0.
            array_count_vanadium[:]=elt_county_vanadium
            array_error_vanadium[:]=elt_counte_vanadium
            #Fill output workspace
            self._owksp.setY(i,array_count_vanadium)
            self._owksp.setE(i,array_error_vanadium)
           
        self.setProperty("OutputWorkspace",self._owksp)      
    
#########################################################################################
# Registration
AlgorithmFactory.subscribe(CalibrateDetectorSensitivities)
