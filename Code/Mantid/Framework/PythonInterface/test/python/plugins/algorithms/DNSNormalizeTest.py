from mantid.kernel import *
import mantid.simpleapi as api
import unittest
from testhelpers import run_algorithm
from mantid.api import AnalysisDataService
from math import pi


class DNSNormalizeTest(unittest.TestCase):

    def setUp(self):
        dataWorkspaceName = "DNSNormalizeTest_Data"
        filename = "dn134011vana.d_dat"
        alg = run_algorithm("LoadDNSLegacy", Filename=filename,
                OutputWorkspace=dataWorkspaceName, Polarisation='y')

        self.test_ws = alg.getPropertyValue("OutputWorkspace")

    def test_NormalizeToDuration(self):
        outputWorkspaceName = "DNSNormalizeTest_NormalizedToDuration"
        alg_test = run_algorithm("DNSNormalize", InputWorkspace=self.test_ws,
                OutputWorkspace=outputWorkspaceName, NormalizeTo='duration')

        self.assertTrue(alg_test.isExecuted())

        # Verify some values
        ws = AnalysisDataService.retrieve(outputWorkspaceName)
        run = ws.getRun()
        duration = run.getProperty('duration').value
        # dimensions
        self.assertEqual(24, ws.getNumberHistograms())
        self.assertEqual(2,  ws.getNumDims())
        # data array
        self.assertAlmostEqual(31461.0/duration, ws.readY(1))
        self.assertAlmostEqual(13340.0/duration, ws.readY(23))
        # sample logs did not change
        self.assertEqual(-8.54, run.getProperty('deterota').value)
        self.assertEqual(8332872, run.getProperty('mon_sum').value)
        self.assertEqual('y', run.getProperty('polarisation').value)
        # check whether detector bank remains rotated
        det = ws.getDetector(1)
        self.assertAlmostEqual(8.54, ws.detectorSignedTwoTheta(det)*180/pi)
        run_algorithm("DeleteWorkspace", Workspace=outputWorkspaceName)
        return

    def test_NormalizeToMonitor(self):
        outputWorkspaceName = "DNSNormalizeTest_NormalizedToMonitor"
        alg_test = run_algorithm("DNSNormalize", InputWorkspace=self.test_ws,
                OutputWorkspace=outputWorkspaceName, NormalizeTo='mon_sum')

        self.assertTrue(alg_test.isExecuted())

        # Verify some values
        ws = AnalysisDataService.retrieve(outputWorkspaceName)
        run = ws.getRun()
        mon_sum = run.getProperty('mon_sum').value
        # dimensions
        self.assertEqual(24, ws.getNumberHistograms())
        self.assertEqual(2,  ws.getNumDims())
        # data array
        self.assertAlmostEqual(31461.0/mon_sum, ws.readY(1))
        self.assertAlmostEqual(13340.0/mon_sum, ws.readY(23))
        # sample logs
        self.assertEqual(-8.54, run.getProperty('deterota').value)
        self.assertEqual(8332872, mon_sum)
        self.assertEqual('y', run.getProperty('polarisation').value)
        # check whether detector bank remains rotated
        det = ws.getDetector(1)
        self.assertAlmostEqual(8.54, ws.detectorSignedTwoTheta(det)*180/pi)
        run_algorithm("DeleteWorkspace", Workspace=outputWorkspaceName)
        return

    def test_Validation(self):
        outputWorkspaceName = "DNSNormalizeTest_TestValidation"
        self.assertRaises(ValueError, api.DNSNormalize, InputWorkspace=self.test_ws,
                          OutputWorkspace=outputWorkspaceName,
                          NormalizeTo='qqq')

    def tearDown(self):
        run_algorithm("DeleteWorkspace", Workspace=self.test_ws)

if __name__ == '__main__':
    unittest.main()
