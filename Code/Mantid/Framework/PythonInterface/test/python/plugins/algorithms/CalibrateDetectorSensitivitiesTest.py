import unittest
from mantid.simpleapi import Load, DeleteWorkspace, CalibrateDetectorSensitivities
from testhelpers import run_algorithm
from mantid.api import AnalysisDataService

class CalibrateDetectorSensitivitiesTest(unittest.TestCase):
    def setUp(self):
        input_ws = Load(Filename="TOFTOFTestdata.nxs")
        self._input_ws = input_ws

    def test_output(self):
        outputWorkspaceName = "output_ws"
        alg_test = run_algorithm("CalibrateDetectorSensitivities",
                                 InputWorkspace=self._input_ws,
                                 OutputWorkspace=outputWorkspaceName)
        wsoutput = AnalysisDataService.retrieve(outputWorkspaceName)
        self.assertTrue(alg_test.isExecuted())

        # Output = Vanadium ws
        self.assertEqual(wsoutput.getRun().getLogData('run_title').value,
                         self._input_ws.getRun().getLogData('run_title').value)

        # Structure of output workspace
        for i in range(wsoutput.getNumberHistograms()):
            self.assertIsNotNone(wsoutput.readY(i)[0])
            for j in range(1, wsoutput.blocksize()):
                self.assertEqual(wsoutput.readY(i)[j], wsoutput.readY(i)[0])

        # Size of output workspace
        self.assertEqual(wsoutput.getNumberHistograms(), self._input_ws.getNumberHistograms())
        self.assertEqual(wsoutput.blocksize(), self._input_ws.blocksize())

        DeleteWorkspace(wsoutput)
        return

    def cleanUp(self):
        if self._input_ws is not None:
            DeleteWorkspace(self._input_ws)

if __name__ == "__main__":
    unittest.main()
