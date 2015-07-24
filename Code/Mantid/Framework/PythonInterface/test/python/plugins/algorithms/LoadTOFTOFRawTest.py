import unittest
from mantid.kernel import *
from mantid.api import *
from mantid import config
from mantid.simpleapi import LoadTOFTOFRaw, DeleteWorkspace
from testhelpers import run_algorithm
from mantid.api import AnalysisDataService


class LoadTOFTOFRawTestTest(unittest.TestCase):
    def test_LoadTOFTOFRaw(self):
        outputWorkspaceName="wsoutput"
        alg_test = run_algorithm("LoadTOFTOFRaw",
                                 Filename="TOFTOFTestdata_0000.raw",
                                 OutputWorkspace=outputWorkspaceName)
        # Execute
        self.assertTrue(alg_test.isExecuted())

        ws = AnalysisDataService.retrieve(outputWorkspaceName)

        # check instrument
        self.assertEqual(ws.getInstrument().getName(), "TOFTOF")

        # check size
        self.assertEqual(ws.getNumberHistograms(), 1006.0)
        self.assertEqual(ws.blocksize(), 1024.0)

        # check some entries of SampleLogs
        run = ws.getRun()
        self.assertEqual(run.getLogData('wavelength').value, 6.0)
        self.assertEqual(float(run.getLogData('chopper_speed').value), 14000.0)
        self.assertEqual(run.getLogData('chopper_ratio').value, 5)
        self.assertEqual(run.getLogData('channel_width').value, 10.5)
        self.assertAlmostEqual(run.getLogData('Ei').value, 2.2723390761570172)
        self.assertEqual(run.getLogData('EPP').value, 578)
        self.assertEqual(run.getLogData('temperature').value, 294.1494)
        self.assertEqual(run.getLogData('duration').value, 3601)
        self.assertEqual(run.getLogData('full_channels').value, 1020)
        self.assertEqual(run.getLogData('monitor_counts').value, 136935)

        # type of output
        self.assertTrue(isinstance(ws, Workspace))

        # units of x-axis
        self.assertEqual(ws.getAxis(0).getUnit().unitID(), "TOF")

        # delete generated files
        AnalysisDataService.remove(outputWorkspaceName)

if __name__ == "__main__":
    unittest.main()
