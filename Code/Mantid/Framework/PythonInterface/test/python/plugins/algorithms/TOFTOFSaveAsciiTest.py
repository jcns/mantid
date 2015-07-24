import unittest
import os
from mantid import config
from testhelpers import run_algorithm
from mantid.simpleapi import Load, LoadEmptyInstrument, CropWorkspace, DeleteWorkspace, TOFTOFSaveAscii
from mantid.api import *
import time
#from mantid.kernel import *


class TOFTOFSaveAsciiTest(unittest.TestCase):
    _test_ws = None
    _inputbad_ws = None

    def setUp(self):
        """
        Create data required for test
        """
        idf = os.path.join(config['instrumentDefinition.directory'], "TOFTOF_Definition.xml")
        ws = LoadEmptyInstrument(Filename=idf)
        ws = CropWorkspace(ws, EndWorkspaceIndex=10)
        ws.getAxis(0).setUnit('DeltaE')
        ws.getAxis(1).setUnit('MomentumTransfer')
        self._test_ws = ws

        inputbad_ws = Load(Filename="TOFTOFTestdata.nxs")
        self._inputbad_ws = inputbad_ws
        #DeleteWorkspace(ws)

    def testBasic(self):
        """
        Test simple execution of algorithm
        """
        alg_test = run_algorithm('TOFTOFSaveAscii',
                                 InputWorkspace=self._test_ws,
                                 OutputFilename='test',
                                 Extension=".txt")
        self.assertTrue(alg_test.isExecuted())

        for i in range(self._test_ws.getNumberHistograms()):
            outfilename = alg_test.getProperty("OutputFilename").value + self._test_ws.name() + "_"+str(i) \
                      + alg_test.getProperty("extension").value
            os.remove(outfilename)

    def testAxesUnits(self):
        """
        Test that the input workspace has the correct units
        """
        self.assertRaises(RuntimeError,
                          run_algorithm,
                          'TOFTOFSaveAscii',
                          InputWorkspace=self._inputbad_ws,
                          OutputFilename="test",
                          Extension=".txt",
                          rethrow=True)
        DeleteWorkspace(self._inputbad_ws)

    def testSuffix(self):
        """
        Test to ensure that outputnames have correctly appended suffix
        """
        alg_test = run_algorithm('TOFTOFSaveAscii', Inputworkspace=self._test_ws, Outputfilename='test')
        self.assertTrue(alg_test.isExecuted())
        self.assertTrue(alg_test.getProperty("extension").value, ".txt")

        for i in range(self._test_ws.getNumberHistograms()):
            outfilename = alg_test.getProperty("OutputFilename").value + self._test_ws.name() + "_"+str(i) \
                          + alg_test.getProperty("extension").value
            os.remove(outfilename)

        alg_test = run_algorithm('TOFTOFSaveAscii', Inputworkspace=self._test_ws, Outputfilename='test',
                                 extension= ".dat")
        self.assertTrue(alg_test.isExecuted())
        self.assertTrue(alg_test.getProperty("extension").value, ".dat")

        for i in range(self._test_ws.getNumberHistograms()):
            outfilename = alg_test.getProperty("OutputFilename").value + self._test_ws.name() + "_"+str(i) \
                          + alg_test.getProperty("extension").value
            os.remove(outfilename)

    def testShapeOutputFile(self):
        """
        Test structure of outputfiles
        """
        alg_test = run_algorithm('TOFTOFSaveAscii', Inputworkspace=self._test_ws, Outputfilename='test')
        self.assertTrue(alg_test.isExecuted())

        for i in range(self._test_ws.getNumberHistograms()):
            outfilename = alg_test.getProperty("OutputFilename").value + self._test_ws.name() + "_"+str(i) \
                      + alg_test.getProperty("extension").value
            try:
                print "Output file is %s. " % outfilename
                ifile = open(outfilename)
                lines = ifile.read()
                ifile.close()
                try:
                    self.assertTrue(len(lines.split()), 4)
                except ValueError as err:
                    print "Unable to determine structure of file"
                    self.assertTrue(False)
                    return
            except IOError as err:
                print "Unable to open file %s. " % outfilename
                self.assertTrue(False)
                return

        for i in range(self._test_ws.getNumberHistograms()):
            outfilename = alg_test.getProperty("OutputFilename").value + self._test_ws.name() + "_"+str(i) \
                          + alg_test.getProperty("extension").value
            os.remove(outfilename)

    def testOverwriteOutputFile(self):
        """
        Test overwriting outputfiles
        """
        #Create empty files
        output_dir = config['defaultsave.directory']
        print 'output_dir', output_dir

        for i in range(self._test_ws.getNumberHistograms()):
            outfilename = output_dir + "test" + self._test_ws.name() + "_" + str(i) + ".txt"
            if not os.path.exists(outfilename):
                open(outfilename, 'a').close()
                print 'creating empty filenames', outfilename

        alg_test = run_algorithm('TOFTOFSaveAscii', Inputworkspace=self._test_ws, Outputfilename='test',
                                 OverwriteExistingFiles=False)
        self.assertTrue(alg_test.isExecuted())

        for i in range(self._test_ws.getNumberHistograms()):
            outfilename = alg_test.getProperty("OutputFilename").value + self._test_ws.name() + "_"+str(i) \
                          + alg_test.getProperty("extension").value
            timestr = time.strftime("%Y%m%d-%H%M%S")
            newoutfilename = alg_test.getProperty("OutputFilename").value +timestr+self._test_ws.name() + "_"+str(i) \
                          + alg_test.getProperty("extension").value
            os.remove(outfilename)
            os.remove(newoutfilename)

    def cleanUp(self):
        """
        Remove data created during test
        """
        if self._test_ws is not None:
            DeleteWorkspace(self._test_ws)


if __name__=="__main__":
    unittest.main()
