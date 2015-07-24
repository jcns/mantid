#pylint: disable=no-init
from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import time
import os


class TOFTOFSaveAscii(PythonAlgorithm):
    """ Save workspace in ascii files
    """
    _FileNameRoot = None
    _FileExtension = None
    _overwrite = False

    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;Utility"

    def name(self):
        """ Return name
        """
        return "TOFTOFSaveAscii"

    def summary(self):
        return "Save workspace in ascii files."

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty(WorkspaceProperty("InputWorkspace", "", direction=Direction.Input), "Input workspace")

        self.declareProperty(FileProperty("OutputFilename", "output", FileAction.Save),
                             doc="Output files of the workspace - split according to q-values.")
        extensions = [".txt", ".dat"]
        self.declareProperty("Extension", ".txt",
                             StringListValidator(extensions), doc="Extension of the output files.")

        self.declareProperty('OverwriteExistingFiles', True, direction=Direction.Input,
                             doc="If output files already exist, overwrite them.")
        return

    def _Function_save_data(self, inputws):
        if inputws.getInstrument().getName() != 'TOFTOF':
            raise ValueError('Wrong instrument')

        # Validator - units
        if inputws.getAxis(1).getUnit().caption() != 'q' or inputws.getAxis(0).getUnit().caption() != 'Energy transfer':
            raise ValueError('Wrong type of workspace. X axis units must be Energy transfer. Y axis units must be q.')

        for i in range(inputws.getNumberHistograms()):
            ofilename = (self._FileNameRoot + "_%d" + self._FileExtension) % i
            if self._overwrite==False and os.path.isfile(ofilename):
                timestr = time.strftime("%Y%m%d-%H%M%S")
                self._FileNameRoot = (self.getProperty("OutputFilename").value+timestr+inputws.getName().split('_')[0])
                ofilename = (self._FileNameRoot + "_%d" + self._FileExtension) % i
            ofile = open(ofilename, 'w')
            xdata = inputws.readX(i)
            ydata = inputws.readY(i)
            edata = inputws.readE(i)
            q_value = inputws.getAxis(1)
            for j in range(inputws.blocksize()):
                ofile.write(str(xdata[j]) + "\t" + str(ydata[j]) + "\t" + str(edata[j])
                         + "\t" + str(q_value.getValue(i)) + "\n")
            ofile.close()

    def PyExec(self):
        """ Main execution body
        """
        wksp = self.getProperty("InputWorkspace").value
        self._FileExtension = self.getProperty("Extension").value

        self._overwrite = self.getProperty("OverwriteExistingFiles").value
        self._FileNameRoot = (self.getProperty("OutputFilename").value+wksp.getName().split('_')[0])
        self._Function_save_data(wksp)

# Register algorithm with Mantid.
AlgorithmFactory.subscribe(TOFTOFSaveAscii)
