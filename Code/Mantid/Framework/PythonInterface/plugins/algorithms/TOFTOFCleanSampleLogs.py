#pylint: disable=no-init
from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *


class TOFTOFCleanSampleLogs(PythonAlgorithm):
    """ Clean the Sample Logs of workspace after merging for TOFTOF instrument
    """
    SameSampleLogsEntries = ['wavelength', 'chopper_speed', 'chopper_ratio', 'channel_width',
                             'Ei', 'EPP']

    ComparedSampleLogsEntries = ['run_title', 'proposal_number', 'proposal_title', 'mode', 'experiment_team']
    #comparedSampleLogsEntries = ['wavelength', 'run_title', 'chopper_speed', 'chopper_ratio',
    #                          'channel_width', 'proposal_title', 'proposal_number', 'experiment_team', 'Ei', 'EPP',
    #                          'mode']

    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;Utility"

    def name(self):
        """ Return summary
        """
        return "TOFTOFCleanSampleLogs"

    def summary(self):
        return "Merge runs and clean the sample logs."

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty("InputWorkspaces", "", validator=StringMandatoryValidator(),
                             doc="Comma separated list of workspaces to use, group"
                                 " workspaces will automatically include all members.")
        self.declareProperty(WorkspaceProperty("OutputWorkspace", "", direction=Direction.Output),
                             doc="Name of the workspace that will contain the merged workspaces "
                                 "with a clean sample logs.")
        return

    def PyExec(self):
        """ Main execution body
        """
        # get list of input workspaces
        wsNames = self.getListInputWorkspaces()
        workspaceCount = len(wsNames)

        wsOutput = self.getPropertyValue("OutputWorkspace")
        if mtd.doesExist(wsOutput):
            DeleteWorkspace(Workspace=wsOutput)

        if workspaceCount > 1:
            # check only first instrument
            if not self.instrumentMatch(wsNames[0]):
                raise ValueError('Wrong instrument')

            list_SampleLogs = self.getSampleLogsEntries(wsNames)

            # canMerge: time + key values in SampleLogs
            self.canMergeLogs(list_SampleLogs)
            self.timingsMatch(wsNames)
            #  Merge runs
            wsOutput = MergeRuns(wsNames)
            run = wsOutput.getRun()
            logs = run.getLogData()
            LogsOutput = {}
            for j in range(len(run.getLogData())):
                entry = logs[j].name
                value = logs[j].value
                LogsOutput[entry] = value

            # Logs entries that could be identical or not:
            # run_title, proposal_title, experiment_team, mode, proposal_number
            FinalListComparedLogs = self.getFinalComparedEntries(list_SampleLogs)

            # Values in Sample Logs to be averaged: temperature
            temperatures = []
            for k in range(len(wsNames)):
                if list_SampleLogs[k].has_key('temperature'):
                    temperatures.append(float(list_SampleLogs[k]['temperature']))
                else:
                    self.log().warning("Temperature sample log is not present in the workspace " + wsNames[k])
            if len(temperatures):
                avgtemp  = sum(temperatures)/len(temperatures)
            else:
                avgtemp = "Not given"

            # avgtemp = 1./len(wsNames)*sum([float(list_SampleLogs[k]['temperature']) for k in range(len(wsNames))])
            # Values in Sample Logs - Min and Max
            tot_duration = max([float(list_SampleLogs[k]['duration']) for k in range(len(wsNames))])
            min_rstart = min([list_SampleLogs[k]['run_start'] for k in range(len(wsNames))])
            max_rend = max([list_SampleLogs[k]['run_end'] for k in range(len(wsNames))])
            min_fchannels = min([list_SampleLogs[k]['full_channels'] for k in range(len(wsNames))])
            lrun_nb = [list_SampleLogs[k]['run_number'] for k in range(len(wsNames))]
            mcounts = sum([int(list_SampleLogs[k]['monitor_counts']) for k in range(len(wsNames))])

            log_names = ['run_title', 'proposal_title', 'experiment_team', 'mode', 'proposal_number', 'temperature',
                         'duration', 'run_start', 'run_end', 'full_channels', 'run_number',
                         'monitor_counts']
            log_values = [FinalListComparedLogs['run_title'], FinalListComparedLogs['proposal_title'],
                          FinalListComparedLogs['experiment_team'], FinalListComparedLogs['mode'],
                          FinalListComparedLogs['proposal_number'], avgtemp, tot_duration,
                          min_rstart, max_rend, min_fchannels, lrun_nb, mcounts]
            AddSampleLogMultiple(Workspace=wsOutput, LogNames=log_names, LogValues=log_values)
            self.setProperty("OutputWorkspace", wsOutput)
            DeleteWorkspace(wsOutput)
        else:
            # If only one input matrix workspace - no merge - no clean sample log to be performed
            if len(wsNames) == 1:
                if not self.instrumentMatch(wsNames[0]):
                    raise ValueError('Wrong instrument')
                RenameWorkspaces(InputWorkspaces=mtd[wsNames[0]].getName(), Workspacenames=wsOutput)
                #wsOutput = wsNames[0]
                self.setProperty("OutputWorkspace", wsOutput)
            else:
                raise ValueError('No input workspace to use')

    def getListInputWorkspaces(self):
        wsInputList = [x.strip() for x in self.getPropertyValue("InputWorkspaces").split(",")]
        wsNames = []
        for wsName in wsInputList:
            # if we cannot find the ws then stop
            if mtd[wsName.strip()] is None:
                raise RuntimeError("Cannot find workspace '" + wsName.strip() + "', aborting")
            # if one item in the input list is a group, list of its components
            if isinstance(mtd[wsName.strip()], WorkspaceGroup):
                wsNames.extend(mtd[wsName.strip()].getNames())
            else:
                wsNames.append(wsName)
        self.log().information("Workspaces to merge: %i" % len(wsNames))
        # if files are not from TOFTOF then stop
        for wsName in wsNames:
            if not self.instrumentMatch(wsName):
                raise ValueError('Wrong instrument')
        return wsNames

    def getFinalComparedEntries(self, listlogs):
        FinalComparedEntries = {}
        for entry in self.ComparedSampleLogsEntries:
            finalentry = list(set([listlogs[k][entry] for k in range(len(listlogs))]))
            if len(finalentry) == 1:
                finalentry = finalentry[0]
            FinalComparedEntries[entry] = finalentry
        return FinalComparedEntries

    def getSampleLogsEntries(self, wsNames):
        list_SampleLogs = []
        for i in range(len(wsNames)):
            list_SampleLogs.append([])
            run = mtd[wsNames[i]].getRun()
            logs = run.getLogData()
            DATA = {}
            for j in range(len(logs)):
                entry = logs[j].name
                value = logs[j].value
                DATA[entry] = value
            list_SampleLogs[i] = DATA
        return list_SampleLogs

    def canMergeLogs(self, listlogs):
        """
        check identical values of some entries in sample logs
        """
        for entry in self.SameSampleLogsEntries:
            list_entries = [listlogs[k][entry] for k in range(len(listlogs))]
            if list_entries.count(list_entries[0]) != len(listlogs):
                raise RuntimeError(entry + " is different between files to be merged', aborting")
        return True

    def instrumentMatch(self, wsName):
        """
        :param wsName:
        :return:
        """
        return mtd[wsName].getInstrument().getName() == 'TOFTOF'

    def timingsMatch(self, wsNames):
        """
        :param wsNames:
        :return:
        """
        for i in range(len(wsNames)):
            leftWorkspace = wsNames[i]
            rightWorkspace = wsNames[i+1]
            leftXData = mtd[leftWorkspace].dataX(0)
            rightXData = mtd[rightWorkspace].dataX(0)
            leftDeltaX = leftXData[0] - leftXData[1]
            rightDeltaX = rightXData[0] - rightXData[1]
            if abs(leftDeltaX - rightDeltaX) >= 1e-4 or abs(rightXData[0] - leftXData[0]) >= 1e-4:
                raise RuntimeError("Timings don't match")
            else:
                return True

# Register algorithm with Mantid.
AlgorithmFactory.subscribe(TOFTOFCleanSampleLogs)
