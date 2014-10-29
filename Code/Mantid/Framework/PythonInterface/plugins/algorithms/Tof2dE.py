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
        return "PythonAlgorithms;Utilities"
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
        self.declareProperty(MatrixWorkspaceProperty("Workspace","",direction=Direction.Input,optional = PropertyMode.Optional), "Input Vanadium workspace (optional)")
        self.declareProperty(WorkspaceProperty("OutputWorkspace","", direction=Direction.Output), "Name the workspace that will contain the result")
        choice_tof = ["Geometry", "FitVanadium","FitSample"]
        self.declareProperty("ChoiceElasticTof", "Geometry",StringListValidator(choice_tof))

        return

    def _FitGaussian(self,ws):
        x_values = ws.readX(1)
        y_values = np.sum(ws.extractY(), axis=0)
        imax=np.argmax(y_values)
        ymax=y_values[imax]
        tryCentre = x_values[imax]
        height = ymax# start guess on peak height
        inx = np.argwhere(y_values>0.5*height)
        sigma = x_values[inx[len(inx)-1][0]]-x_values[inx[0][0]] # start guess on peak width
    #    ## Function to fit
        myFunc = 'name=Gaussian, Height='+str(height)+', PeakCentre='+str(tryCentre)+', Sigma='+str(sigma)
    #    ##Fitting window
        startx = tryCentre-10.*sigma
        endx = tryCentre+10.*sigma
        ##Run fitting of vector not workspace
        dataWS = CreateWorkspace(DataX=x_values, DataY=y_values)
        fitStatus, chiSq, covarianceTable, paramTable, fitWorkspace = Fit(InputWorkspace=dataWS, \
        StartX = startx, EndX=endx, Output='fitGaussian', Function=myFunc)
        return paramTable.column(1)[1]
    
    def _FitLorentzian(self,ws):
        x_values = ws.readX(1)
        y_values = np.sum(ws.extractY(), axis=0)
        imax=np.argmax(y_values)
        ymax=y_values[imax]
        tryCentre = x_values[imax]
        height = ymax# start guess on peak height
        inx = np.argwhere(y_values>0.5*height)
        sigma = x_values[inx[len(inx)-1][0]]-x_values[inx[0][0]] # start guess on peak width
    #    ## Function to fit
        myFunc = 'name=LinearBackground, A0=0; name=Lorentzian, Amplitude='+str(height)+\
        ', PeakCentre='+str(tryCentre)+', FWHM='+str(sigma)
    #    ##Fitting window
        startx = tryCentre-10.*sigma
        endx = tryCentre+10.*sigma
        ##Run fitting of vector not workspace
        dataWS = CreateWorkspace(DataX=x_values, DataY=y_values)
        fitStatus, chiSq, covarianceTable, paramTable, fitWorkspace = Fit(InputWorkspace=dataWS,\
        StartX = startx, EndX=endx, Output='fitLorentzian', Function=myFunc,\
        constraints='f1.PeakCentre>0,f1.FWHM>0')
        return paramTable.column(1)[1]

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
 
        if a=='Geometry':
            # tof_elastic from header of raw datafile
            print a
            tof_elastic=float(run.getLogData('EPP').value)*float(run.getLogData('channel_width').value) #in microsecs
        if a=='FitSample':
            print a
            tof_elastic = self._FitLorentzian(self._wksp)
        if a=='FitVanadium':
            self._wkspvana = self.getProperty("Workspace").value
            print a
            tof_elastic = self._FitGaussian(self._wkspvana)
        
        print float(run.getLogData('EPP').value)*float(run.getLogData('channel_width').value),tof_elastic
        sample = self._wksp.getInstrument().getSample() 
        samplePos = sample.getPos()
        sourcePos = self._wksp.getInstrument().getSource().getPos()
        Lsd = self._wksp.getInstrument().getDetector(1).getDistance(sample)

        nb_block = self._wksp.blocksize()
        nb_hist = self._wksp.getNumberHistograms()

        self._owksp = self._wksp+0.

        arrayx=np.zeros(nb_block+1)
        print tof_elastic
        for i in range(nb_block+1):
            arrayx[i]=0.5*sp.constants.m_n*Lsd**2*(1/self._wksp.readX(1)[i]**2-1/tof_elastic**2)*10.**15/sp.constants.eV
            print arrayx[i]
     
        for j in range(nb_hist):
            self._owksp.setX(j,arrayx)
        
        self._owksp.getAxis(0).setUnit('DeltaE')
           
        self.setProperty("OutputWorkspace",self._owksp)      
    
#########################################################################################
# Registration
AlgorithmFactory.subscribe(Tof2dE)
