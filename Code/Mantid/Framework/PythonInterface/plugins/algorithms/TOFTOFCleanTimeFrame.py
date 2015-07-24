#pylint: disable=no-init
from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *


class TOFTOFCleanTimeFrame(PythonAlgorithm):
    """ Crop empty time channels
    """

    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;Utility"

    def name(self):
        """ Return summary
        """
        return "TOFTOFCleanTimeFrame"

    def summary(self):
        return "Crop empty time channels."

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty(WorkspaceProperty("InputWorkspace", "", direction=Direction.Input), doc="Input workspace.")
        self.declareProperty(WorkspaceProperty("OutputWorkspace", "", direction=Direction.Output),
                             doc="Name of the workspace that will contain the results")
        return

    def PyExec(self):
        """ Main execution body
        """
        wsInput = self.getProperty("InputWorkspace").value
        if wsInput.getInstrument().getName() != 'TOFTOF':
            raise ValueError('Wrong instrument')

        if wsInput.getAxis(0).getUnit().caption() != 'Time-of-flight':
            raise ValueError('Wrong type of workspace. X axis units must be time of flight.')
        channel_width = float(wsInput.getRun().getLogData('channel_width').value)
        full_channels = float(wsInput.getRun().getLogData('full_channels').value)

        outputws = CropWorkspace(wsInput, XMin=0.*channel_width, XMax=full_channels*channel_width)
        self.setProperty("OutputWorkspace", outputws)

        DeleteWorkspace(Workspace=outputws)

# Register algorithm with Mantid.
AlgorithmFactory.subscribe(TOFTOFCleanTimeFrame)
