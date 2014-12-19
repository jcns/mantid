from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import numpy as np
import scipy as sp
import re
#import os

class SaveMLZAscii(PythonAlgorithm):
    """ Save workspace in ascii files
    """
    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;MLZ"
    def name(self):
        """ Return name
        """
        return "SaveMLZAscii"

    def summary(self):
        return "Save workspace in ascii files."

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty(WorkspaceProperty("InputWorkspace","",direction=Direction.Input), "Input workspace")
        
        self.declareProperty(FileProperty("OutputFilename","", FileAction.Save),
            doc="Output files of the workspace - split according to q-values.")
        self.declareProperty(FileProperty("OutputDirectory","", FileAction.OptionalDirectory), doc="Directory to write the output files in [optional]. Default = default save directory")
        
        extensions = [ ".txt", ".dat"]
        self.declareProperty("Extension", ".txt",
                             StringListValidator(extensions),doc="Extension of the output files. Default='.txt")
        return


    def PyExec(self):
        """ Main execution body
        """
 
        wksp = self.getProperty("InputWorkspace").value
        FileName = self.getProperty("OutputFilename").value
        path = self.getProperty("OutputDirectory").value
        FileExtension = self.getProperty("Extension").value
        
        if (wksp.getInstrument().getName() != 'TOFTOF'):
            raise ValueError('Wrong instrument')
        
        #Validator - units
        if (wksp.getAxis(1).getUnit().caption() != 'q' or wksp.getAxis(0).getUnit().caption() !='Energy transfer'):
            raise ValueError('Wrong type of workspace. Y axis units must be q.')
        
        for i in range(wksp.getNumberHistograms()):
            outputfile = (FileName+"_%d"+FileExtension)%i
            fp = open(outputfile,'w')
            x = wksp.readX(i)
            y = wksp.readY(i)
            e = wksp.readE(i)
            q_value = wksp.getAxis(1)
            
            for j in range(wksp.blocksize()):
                fp.write( str(x[j])+"\t"+str(y[j])+"\t"+str(e[j])+"\t"+str(q_value.getValue(i))+"\n"  )
        
            fp.closed

        
#########################################################################################
# Registration
AlgorithmFactory.subscribe(SaveMLZAscii)












