from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import numpy as np
import scipy as sp
import re
from collections import Counter

class RemoveExtraDetectors(PythonAlgorithm):
    """ Remove detectors with no counts, which have not been masked 
    """
    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;MLZ"
    def name(self):
        """ Return summary
        """
        return "RemoveExtraDetectors"

    def summary(self):
        return "Remove detectors with no counts, which have not been masked ."

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty("InputWorkspaces","", validator=StringMandatoryValidator(), doc="Comma separated list of workspaces to use, group workspaces will automatically include all members.")
        self.declareProperty(IntArrayProperty("OutputList", values=[], direction=Direction.Output),"Detector IDs that have to be masked. They have no counts.")
        return


    def PyExec(self):
        """ Main execution body
        """

         # get parameter values
        wsInputList = [x.strip() for x in self.getPropertyValue("InputWorkspaces").split(",") ]
       
        #get the workspace list
        wsNames = []
        for wsName in wsInputList: 
            #check the ws is in mantid
            ws = mtd[wsName.strip()]
            #if we cannot find the ws then stop
            if ws == None:
                raise RuntimeError ("Cannot find workspace '" + wsName.strip() + "', aborting")
            else:
                #if files are not from TOFTOF then stop
                if (ws.getInstrument().getName() != 'TOFTOF'):
                    raise ValueError('Wrong instrument')
            if isinstance(ws, WorkspaceGroup):
                wsNames.extend(ws.getNames())
            else:
                wsNames.append(wsName)
        
        ExtraMaskedDetectors=[]
        #Loop on all input workspaces
        for i in range(len(wsNames)):
            wsName=mtd[wsNames[i]]
            list=[max(wsName.readY(j)) for j in range(wsName.getNumberHistograms()) ]
            ExtraMaskedDetectors.extend([i for i, j in enumerate(list) if (j==0 and not wsName.getInstrument().getDetector(i).isMasked())])
        
        #print ExtraMaskedDetectors
        
        AdditionalMaskDetectors = self.getPropertyValue("OutputList")
        if all(x==len(wsNames) for x in Counter(ExtraMaskedDetectors).values()):
            AdditionalMaskDetectors=  Counter(ExtraMaskedDetectors).keys()
            #map(int, Counter(ExtraMaskedDetectors).keys())
        #print AdditionalMaskDetectors
            
        if AdditionalMaskDetectors is not None:
            self.setProperty("OutputList", AdditionalMaskDetectors)

#########################################################################################
# Registration
AlgorithmFactory.subscribe(RemoveExtraDetectors)




