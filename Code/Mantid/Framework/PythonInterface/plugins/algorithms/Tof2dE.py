from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import numpy as np
from scipy.integrate import quad
import scipy as sp
import re

# Test for keyword Vanadium or vanadium in Title - compulsory entries
class Tof2dE(PythonAlgorithm):
    """ Calculate energy transfer using elastic tof
    """
    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;MLZ"
    def name(self):
        """ Return summary
        """
        return "Tof2dE"

    def summary(self):
        return "Calculate energy transfer using elastic tof. Three choices to calculate tof: geometry (EPP guess - default), fit from vanadium or fit from sample."

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty(WorkspaceProperty("InputWorkspace","",direction=Direction.Input), "Input Sample workspace")
        #Optional but required if choice of tof_elastic from Vanadium ws or file
        self.declareProperty(MatrixWorkspaceProperty("Workspace","", direction=Direction.Input,optional = PropertyMode.Optional), "Input Vanadium workspace (optional)")
        self.declareProperty(WorkspaceProperty("OutputWorkspace","", direction=Direction.Output), "Name the workspace that will contain the result")
        choice_tof = ["Geometry", "FitVanadium","FitSample"]
        self.declareProperty("ChoiceElasticTof", "Geometry",StringListValidator(choice_tof))

        return


    def _FitGaussiang(self,ws):
        nb_hist = ws.getNumberHistograms()
        TableFit=np.zeros(nb_hist)
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
                print i, 'initial guess: height ',height,', centre: ',tryCentre,'sigma ', sigma,'startX',tryCentre-5.*sigma,'endX',tryCentre+5.*sigma  
                fitAlg.setProperty('Function','name=Gaussian, Height='+str(height)+', PeakCentre='+str(tryCentre)+', Sigma='+str(sigma))
                fitAlg.setProperty('InputWorkspace', ws) 
                fitAlg.setProperty('WorkspaceIndex', i)
                fitAlg.setProperty('StartX', tryCentre-10.*sigma)
                fitAlg.setProperty('EndX', tryCentre+10.*sigma)
                fitAlg.setProperty('Output','fitGaussianTof2dE')
                fitAlg.setProperty('CreateOutput',True)
                fitAlg.execute()
                paramTable = fitAlg.getProperty('OutputParameters').value
              
                TableFit[i]=paramTable.column(1)[1]
                #print i, paramTable.column(1)[0],paramTable.column(2)[0],paramTable.column(1)[1],paramTable.column(2)[1],paramTable.column(1)[2],paramTable.column(2)[2]
            else:
                TableFit[i]=0.
        return TableFit

    def _FitLorentziang(self,ws):
        nb_hist = ws.getNumberHistograms()
        TableFit=np.zeros(nb_hist)
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
                print "First guess for index", i, ": height",height ,"centre:" ,tryCentre ,"sigma",sigma,'startX',tryCentre-5.*sigma,'endX',tryCentre+5.*sigma
                fitAlg = self.createChildAlgorithm('Fit')  
                fitAlg.setProperty('Function','name=LinearBackground, A0=0; name=Lorentzian, Amplitude='+str(height)+\
        ', PeakCentre='+str(tryCentre)+', FWHM='+str(sigma))
                fitAlg.setProperty('InputWorkspace', ws) 
                fitAlg.setProperty('WorkspaceIndex', i)
                fitAlg.setProperty('StartX', tryCentre-5.*sigma)
                fitAlg.setProperty('EndX', tryCentre+5.*sigma)
                
                fitAlg.setProperty('CreateOutput',True)
                fitAlg.setProperty('Output','fitLorentzian')
                fitAlg.setProperty('constraints','f1.PeakCentre>0,f1.FWHM>0')
                fitAlg.execute()
                paramTable = fitAlg.getProperty('OutputParameters').value
                TableFit[i]=paramTable.column(1)[3]
                print i, paramTable.column(1)[0],paramTable.column(1)[1],paramTable.column(1)[2],paramTable.column(1)[3],paramTable.column(1)[4],
            else:
                TableFit[i]=0.
        return TableFit
    

    def PyExec(self):
        """ Main execution body
        """
        self._wksp = self.getProperty("InputWorkspace").value
        self._owksp = self.getProperty("OutputWorkspace").value
        
        #check TOFTOF
        if (self._wksp.getInstrument().getName() != 'TOFTOF'):
            raise ValueError('Wrong instrument')

        run=self._wksp.getRun()
        a=self.getProperty("ChoiceElasticTof").value
        
        nb_block = self._wksp.blocksize()
        nb_hist = self._wksp.getNumberHistograms()
        
        if a=='Geometry':
            # tof_elastic from header of raw datafile
            tof_elastic=np.zeros(nb_hist)
            tof_elastic[:] = float(run.getLogData('EPP').value)*float(run.getLogData('channel_width').value) #in microsecs

        if a=='FitSample':
            tof_elastic = self._FitLorentziang(self._wksp)
        if a=='FitVanadium':
            self._wkspvana = self.getProperty("Workspace").value
            tof_elastic = self._FitGaussiang(self._wkspvana)
        
        sample = self._wksp.getInstrument().getSample() 
        samplePos = sample.getPos()
        sourcePos = self._wksp.getInstrument().getSource().getPos()
        Lsd = self._wksp.getInstrument().getDetector(1).getDistance(sample)

        self._owksp = self._wksp+0.

        arrayx=np.zeros(nb_block+1) # will be filled for each histogram

        dx = sp.array([self._wksp.readX(1)[i]-self._wksp.readX(1)[i-1] for i in range(1,len(arrayx))])
        arrayynorm=sp.array([(self._wksp.readX(1)[i]/1.e6)**3*sp.constants.eV*1.e3/(sp.constants.m_n*Lsd**2*dx[i]) for i in range(nb_block)])
        
        for j in range(nb_hist):
            if tof_elastic[j] != 0.:
                for i in range(nb_block+1):
                    arrayx[i]=0.5*sp.constants.m_n*Lsd**2*(1./self._wksp.readX(j)[i]**2-1./tof_elastic[j]**2)*10.**15/sp.constants.eV
            self._owksp.setX(j,arrayx)
            newy=arrayynorm*self._owksp.readY(j)
            newe=arrayynorm*self._owksp.readE(j)
            self._owksp.setY(j,newy)
            self._owksp.setE(j,newe)
              
        self._owksp.getAxis(0).setUnit('DeltaE')
           
        self.setProperty("OutputWorkspace",self._owksp)      
    
#########################################################################################
# Registration
AlgorithmFactory.subscribe(Tof2dE)
