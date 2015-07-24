import unittest
from mantid.simpleapi import Load, DeleteWorkspace, TOFTOFConvertTofToDeltaE, CropWorkspace
from testhelpers import run_algorithm
from mantid.api import AnalysisDataService

class TOFTOFConvertTofToDeltaETest(unittest.TestCase):
    def setUp(self):
        #create workspace with right units: xaxis=tof
        input_ws = Load(Filename="TOFTOFTestdata.nxs")
        # crop input workspace not to slow down the unit tests
        input_ws = CropWorkspace(input_ws, EndWorkspaceIndex=10)
        self._input_ws = input_ws

    def test_basicrun(self):
        # run algo
        OutputWorkspaceName="outputws"
        alg_test = run_algorithm("TOFTOFConvertTofToDeltaE",
                                 InputWorkspace=self._input_ws,
                                 OutputWorkspace=OutputWorkspaceName,
                                 ChoiceElasticTof="Geometry")
        wsoutput = AnalysisDataService.retrieve(OutputWorkspaceName)
        # execution of algorithm
        self.assertTrue(alg_test.isExecuted())
        # unit of output
        self.assertEqual(wsoutput.getAxis(0).getUnit().unitID(), "DeltaE")
        # shape of output compared to input
        self.assertEqual(wsoutput.getNumberHistograms(), self._input_ws.getNumberHistograms())
        self.assertEqual(wsoutput.blocksize(), self._input_ws.blocksize())
        self.assertEqual(wsoutput.getInstrument().getName(), "TOFTOF")
        DeleteWorkspace(wsoutput)

    def test_defaultsetup(self):
        OutputWorkspaceName="outputws"
        alg_test = run_algorithm("TOFTOFConvertTofToDeltaE",
                                 InputWorkspace=self._input_ws,
                                 OutputWorkspace=OutputWorkspaceName)
        self.assertTrue(alg_test.isExecuted())
        self.assertEqual(alg_test.getProperty("ChoiceElasticTof").value, "Geometry")
        wsoutput = AnalysisDataService.retrieve(OutputWorkspaceName)
        DeleteWorkspace(wsoutput)

    # Test options to calculate tof elastic
    def test_calculationtofelastic(self):
        options_tof = ["Geometry", "FitVanadium", "FitSample"]
        for choice in options_tof:
            OutputWorkspaceName="outputws"
            alg_test = run_algorithm("TOFTOFConvertTofToDeltaE", InputWorkspace=self._input_ws,
                                     WorkspaceVanadium=self._input_ws,
                                     OutputWorkspace=OutputWorkspaceName,
                                     ChoiceElasticTof=choice)
            self.assertTrue(alg_test.isExecuted())
            wsoutput = AnalysisDataService.retrieve(OutputWorkspaceName)
            DeleteWorkspace(wsoutput)

    def cleanUp(self):
        if self._input_ws is not None:
            DeleteWorkspace(self._input_ws)

if __name__=="__main__":
    unittest.main()
