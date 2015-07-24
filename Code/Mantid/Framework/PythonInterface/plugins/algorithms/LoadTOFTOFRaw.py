#pylint: disable=no-init,invalid-name
import re
from mantid.simpleapi import *
from mantid.api import *
from mantid.kernel import *
import numpy as np
import scipy as sp
import os
#from string import split
from datetime import datetime
import pytz


class LoadTOFTOFRaw(PythonAlgorithm):
    """ Load raw datafile for TOFTOF instrument
    """
    _masked_detectors = None
    _owksp = None
    NumOfDetectors = None
    Data = None
    ChannelWidth = None

    def category(self):
        """ Return category
        """
        return "PythonAlgorithms"

    def name(self):
        """ Return summary
        """
        return "LoadTOFTOFRaw"

    def summary(self):
        return "Load raw datafile for TOFTOF instrument"

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty(FileProperty("Filename", "", FileAction.Load, ["0000.raw"]),
                             "File path of the Data file(s) to load")
        self.declareProperty(WorkspaceProperty("OutputWorkspace", "", Direction.Output),
                             "The name to use for the output workspace")
        return

    def PyExec(self):
        """ Main execution body
        """
        config['default.facility'] = "MLZ"
        config['default.instrument'] = "TOFTOF"
        filenameData = self.getPropertyValue("Filename")
        self.Data = self._read_file(filenameData)
        nblock = int(self.Data['NumOfChannels'])

        self.ChannelWidth = float(self.Data['TOF_ChannelWidth'])*50.e-3

        dataX = np.zeros(nblock+1)
        for i in range(nblock+1):
            dataX[i] = self.ChannelWidth*(i+0.5)

        # run function and write data
        sdata = self._sort_detectors_and_counts()
        nhist = int(self.NumOfDetectors)
        dataY = sdata['SortedCounts']

        dataE = np.sqrt(dataY)
        self._owksp = CreateWorkspace(DataX=dataX, DataY=dataY, DataE=dataE, NSpec=nhist, UnitX="TOF",
                                      YUnitLabel="counts")

        self._loadIDF()
        self._loadRunDetails()
        self._masked_detectors = sdata['MaskedDetectors']
         # Apply mask to 'None' detectors
        MaskDetectors(Workspace=self._owksp, DetectorList=self._masked_detectors)

        self.setProperty("OutputWorkspace", self._owksp)
        DeleteWorkspace(self._owksp)

    def _loadIDF(self):
        inst_name = 'TOFTOF'
        # self.log().debug("Instrument name: TOFTOF")
        inst_dir = config.getInstrumentDirectory()
        inst_file = os.path.join(inst_dir, inst_name + "_Definition.xml")
        LoadInstrument(Workspace=self._owksp, Filename=inst_file)

    def _loadRunDetails(self):
        name = re.split('/', self.Data["FileName"])
        run_num = re.split('_', name[len(name)-1])[0]
        self._owksp.run().addProperty("run_number", run_num, True)

        ##IDate = re.split("\.", self.Data['StartDate'])
        IDate = list(map(int, self.Data['StartDate'].split('.')))
        ITime = list(map(int, self.Data['StartTime'].split(':')))
        start_time = datetime(IDate[2], IDate[1], IDate[0], ITime[0], ITime[1], ITime[2],
                              tzinfo=pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%dT%H:%M:%S%z')
        self._owksp.run().addProperty("run_start", start_time, True)

        FDate = list(map(int, self.Data['SavingDate'].split('.')))
        FTime = list(map(int, self.Data['SavingTime'].split(':')))
        end_time = datetime(FDate[2], FDate[1], FDate[0], FTime[0], FTime[1], FTime[2],
                            tzinfo=pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%dT%H:%M:%S%z')
        self._owksp.run().addProperty("run_end", end_time, True)

        wavelength = float(self.Data['Chopper_Wavelength'].split()[0])
        self._owksp.run().addProperty("wavelength", wavelength, 'angstrom', True)  # check if could be read from file

        ei = (sp.constants.h*sp.constants.h)/(2.*sp.constants.m_n * wavelength**2*1e-20)/sp.constants.eV*1.e3
        self._owksp.run().addProperty("Ei", ei, 'meV', True)

        ftr = [3600, 60, 1]
        duration = sum([a*b for a, b in zip(ftr, map(int, self.Data['SavingTime'].split(':')))]) \
                   - sum([a*b for a, b in zip(ftr, map(int, self.Data['StartTime'].split(':')))])

        self._owksp.run().addProperty("duration", float(duration), 'second', True)

        mode = self.Data['TOF_MMode']
        self._owksp.run().addProperty("mode", mode, True)

        title = self.Data['Title']
        self._owksp.run().addProperty("run_title", title, True)

        # Check if temperature is defined
        if not 'AverageSampleTemperature' in self.Data:
            temperature = 293.
        elif self.Data['AverageSampleTemperature'] == {}:
            temperature = 293.
        else:
            temperature = float(self.Data['AverageSampleTemperature'].split()[0])
        self._owksp.run().addProperty("temperature", float(temperature), 'kelvin', True)

        monitorCounts = self.Data['MonitorCounts']
        self._owksp.run().addProperty("monitor_counts", float(monitorCounts), True)

        chopper_speed = self.Data['Chopper_Speed'].split()[0]
        self._owksp.run().addProperty("chopper_speed", chopper_speed, self.Data['Chopper_Speed'].split()[1], True)

        chopper_ratio = self.Data['Chopper_Ratio']
        self._owksp.run().addProperty("chopper_ratio", float(chopper_ratio), True)

        self._owksp.run().addProperty("channel_width", self.ChannelWidth, 'microsecond', True)

        #Calculate number of full time channels - use to crop workspace - S. Busch method
        # channelWidth in microsec
        full_channels = sp.floor(30.*float(chopper_ratio)/float(chopper_speed)*1.e6/float(self.ChannelWidth))
        self._owksp.run().addProperty("full_channels", float(full_channels), True)

        proposal_title = self.Data['ProposalTitle']
        self._owksp.run().addProperty("proposal_title", proposal_title, True)

        proposal_number = self.Data['ProposalNr']
        self._owksp.run().addProperty("proposal_number", float(proposal_number), True)

        if 'ExperimentTeam' in self.Data:
            self._owksp.run().addProperty("experiment_team", self.Data['ExperimentTeam'], True)

        monitorElasticPeakPosition = self.Data['TOF_ChannelOfElasticLine_Guess']
        self._owksp.run().addProperty("EPP", float(monitorElasticPeakPosition), True)

    def _read_file(self, filename):
        fp = open(filename)
        # Read parameter section (each line has form 'keyword: value').
        DATA = {}
        for line in fp:
            if line.startswith('aDetInfo'):
                break
            temp = re.split(":", line, maxsplit=1)
            #temp = map(strip, split(line, sep=":", maxsplit=1))
            entry = temp[0].strip()
            value = temp[1].strip()
            DATA[entry] = value

        # Read detector description section.
        DATA['aDetInfo'] = []
        for line in fp:
            if line[0] == '#':
                continue
            if line.startswith('aData'):
                break
            DATA['aDetInfo'].append(line)

        # Read neutron counts section.
        DATA['aData'] = []
        for line in fp:
            DATA['aData'].append(sp.array(map(int, line.split())))
            #DATA['aData'].append(sp.array(map(int, split(line))))
        fp.close()
        return DATA

    def _sort_detectors_and_counts(self):
        # Read info about detectors
        block = self.Data['aDetInfo']
        nDet = len(block)
        self.NumOfDetectors = nDet
        detNr = np.zeros(nDet, dtype='int32')
        theta = np.zeros(nDet, dtype='float32')
        eleTotal = np.zeros(nDet, dtype='int32')
        list_of_none_detectors = []
        sortedData0 = {}
        pattern = re.compile(r'''((?:[^'\s+]|'[^']*')+)''')   # split, escaping quoted
        for i in range(nDet):
            line = block[i]
            entry = pattern.split(line)[1::2]
            _detNr = int(entry[0])
            if not _detNr == i + 1:
                raise Exception('Unexpected detector number %d instead of %d in detector info line %d: "%s"' %
                                (detNr, i + 1, i, line))
            detNr[i] = _detNr
            theta[i] = float(entry[5])
            eleTotal[i] = int(entry[12])
            # Determine unsorted list of 'None' detectors
            if entry[13] == "'None'" and max(self.Data['aData'][eleTotal[i] - 1]) == 0:
                list_of_none_detectors.append(_detNr)
        #Sort detectors' data according by angle (array theta)
        inds = theta.argsort()
        detNr = detNr[inds]
        eleTotal = eleTotal[inds]
        # Sorted counts
        countsorted = []
        for i in range(nDet):
            countsorted.append(self.Data['aData'][eleTotal[i]-1])
        countsorted = np.array(countsorted, dtype='int32').reshape(1, nDet*int(self.Data['NumOfChannels']))
        #print countsorted
        sortedData0['SortedCounts'] = countsorted
        # list new index for None detectors (linked with sorted angles and not detector's numbers)
        list_of_none_detectors_angles = []
        for i in range(len(list_of_none_detectors)):
            list_of_none_detectors_angles.append(int(np.where(detNr == list_of_none_detectors[i])[0]))
        list_of_none_detectors_angles.sort()
        sortedData0['MaskedDetectors'] = list_of_none_detectors_angles
        return sortedData0

# Registration
AlgorithmFactory.subscribe(LoadTOFTOFRaw)
