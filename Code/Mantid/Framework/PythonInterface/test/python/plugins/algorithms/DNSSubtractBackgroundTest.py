# import mantid.simpleapi as api
import unittest
from testhelpers import run_algorithm
from mantid.api import AnalysisDataService
from math import pi


class DNSSubtractBackgroundTest(unittest.TestCase):

    def setUp(self):
        dataWorkspaceName = "DNSSubtractBackgroundTest_Data"
        bkgWorkspaceName = "DNSSubtractBackgroundTest_Bkg"
        filename_data = "dn134011vana.d_dat"
        filename_bkg = "dn134031leer.d_dat"
        alg = run_algorithm("LoadDNSLegacy", Filename=filename_data,
                            OutputWorkspace=dataWorkspaceName, Polarisation='y')
        alg2 = run_algorithm("LoadDNSLegacy", Filename=filename_bkg,
                             OutputWorkspace=bkgWorkspaceName, Polarisation='x')

        self.test_dataws = alg.getPropertyValue("OutputWorkspace")
        self.test_bkgws = alg2.getPropertyValue("OutputWorkspace")

    def test_SubtractNormalizedToDuration(self):
        outputWorkspaceName = "DNSSubtractBkgTest_NormalizedToDuration"
        alg_test = run_algorithm("DNSSubtractBackground", DataWorkspace=self.test_dataws,
                                 BackgroundWorkspace=self.test_bkgws,
                                 OutputWorkspace=outputWorkspaceName, NormalizeBy='duration')

        self.assertTrue(alg_test.isExecuted())
        self.assertTrue(AnalysisDataService.doesExist(outputWorkspaceName))

        # Verify some values
        ws = AnalysisDataService.retrieve(outputWorkspaceName)
        run = ws.getRun()
        duration = run.getProperty('duration').value
        # dimensions
        self.assertEqual(24, ws.getNumberHistograms())
        self.assertEqual(2,  ws.getNumDims())
        # data array
        self.assertAlmostEqual(46.73766667, ws.readY(1))
        self.assertAlmostEqual(19.976, ws.readY(23), places=3)
        # sample logs did not change
        self.assertEqual(-8.54, run.getProperty('deterota').value)
        self.assertEqual(8332872, run.getProperty('mon_sum').value)
        self.assertEqual(600, duration)
        self.assertEqual('y', run.getProperty('polarisation').value)
        # check whether detector bank remains rotated
        det = ws.getDetector(1)
        self.assertAlmostEqual(8.54, ws.detectorSignedTwoTheta(det)*180/pi)
        run_algorithm("DeleteWorkspace", Workspace=outputWorkspaceName)
        return

    def test_SubtractNormalizedToMonitor(self):
        outputWorkspaceName = "DNSSubtractBkgTest_NormalizedToMonitor"
        alg_test = run_algorithm("DNSSubtractBackground", DataWorkspace=self.test_dataws,
                                 BackgroundWorkspace=self.test_bkgws,
                                 OutputWorkspace=outputWorkspaceName, NormalizeBy='mon_sum')

        self.assertTrue(alg_test.isExecuted())
        self.assertTrue(AnalysisDataService.doesExist(outputWorkspaceName))

        # Verify some values
        ws = AnalysisDataService.retrieve(outputWorkspaceName)
        run = ws.getRun()
        mon_sum = run.getProperty('mon_sum').value
        # dimensions
        self.assertEqual(24, ws.getNumberHistograms())
        self.assertEqual(2,  ws.getNumDims())
        # data array
        self.assertAlmostEqual(0.00361599, ws.readY(1))
        self.assertAlmostEqual(0.00153768, ws.readY(23))
        # sample logs
        self.assertEqual(-8.54, run.getProperty('deterota').value)
        self.assertEqual(8332872, mon_sum)
        self.assertEqual('y', run.getProperty('polarisation').value)
        # check whether detector bank remains rotated
        det = ws.getDetector(1)
        self.assertAlmostEqual(8.54, ws.detectorSignedTwoTheta(det)*180/pi)
        run_algorithm("DeleteWorkspace", Workspace=outputWorkspaceName)
        return

    def test_SubstractBackgroundNoLogs(self):
        """
        tests whether the algorithm will run successfully
        if some sample logs are absent
        """
        run_algorithm("DeleteLog", Workspace=self.test_dataws, Name='deterota')
        outputWorkspaceName = "DNSSubtractBkgTest_NoDeterotaLog"
        alg_test = run_algorithm("DNSSubtractBackground", DataWorkspace=self.test_dataws,
                                 BackgroundWorkspace=self.test_bkgws,
                                 OutputWorkspace=outputWorkspaceName, NormalizeBy='duration')

        self.assertTrue(alg_test.isExecuted())
        self.assertTrue(AnalysisDataService.doesExist(outputWorkspaceName))
        run_algorithm("DeleteWorkspace", Workspace=outputWorkspaceName)

        return

    def tearDown(self):
        run_algorithm("DeleteWorkspace", Workspace=self.test_dataws)
        run_algorithm("DeleteWorkspace", Workspace=self.test_bkgws)

if __name__ == '__main__':
    unittest.main()
