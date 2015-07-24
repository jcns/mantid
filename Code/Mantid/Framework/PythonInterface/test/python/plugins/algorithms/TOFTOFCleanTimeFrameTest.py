import unittest
from mantid.simpleapi import Load, DeleteWorkspace, TOFTOFCleanTimeFrame
from testhelpers import run_algorithm
from mantid.api import AnalysisDataService
# check this import
from mantid.kernel import *


class TOFTOFCleanTimeFrameTest(unittest.TestCase):

    _input_ws = None
    _cropped_ws = None

    def setUp(self):
        input_ws = Load(Filename="TOFTOFTestdata.nxs")
        self._input_ws = input_ws

    def test_basicrun(self):
        OutputWorkspaceName = "cropped_ws"
        alg_test = run_algorithm("TOFTOFCleanTimeFrame",
                                 InputWorkspace=self._input_ws,
                                 OutputWorkspace=OutputWorkspaceName)
        self._cropped_ws = AnalysisDataService.retrieve(OutputWorkspaceName)
        self.assertTrue(alg_test.isExecuted())

        run = self._cropped_ws.getRun()
        # check existence of required entries in logs
        self.assertTrue('full_channels' in run.keys())
        self.assertTrue('channel_width' in run.keys())
        # check their values
        full_channels = float(run.getLogData('full_channels').value)
        channel_width = float(run.getLogData('channel_width').value)
        self.assertTrue(full_channels > 0.)
        self.assertTrue(channel_width > 0.)
        # check instrument
        self.assertEqual(self._cropped_ws.getInstrument().getName(), "TOFTOF")
        # check unit horizontal axis
        self.assertEqual(self._cropped_ws.getAxis(0).getUnit().unitID(), 'TOF')
        # check length of cropped ws
        self.assertEqual(len(self._cropped_ws.readX(0)), int(full_channels))

    def cleanUp(self):
        if self._input_ws is not None:
            DeleteWorkspace(self._input_ws)
        if self._cropped_ws is not None:
            DeleteWorkspace(self._cropped_ws)

if __name__ == "__main__":
    unittest.main()
