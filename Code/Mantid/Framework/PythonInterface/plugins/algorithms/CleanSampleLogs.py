from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import numpy as np
import scipy as sp
import re

class CleanSampleLogs(PythonAlgorithm):
    """ Clean the Sample Logs of workspace after merging
    """
    def category(self):
        """ Return category
        """
        return "PythonAlgorithms;MLZ"
    def name(self):
        """ Return summary
        """
        return "CleanSampleLogs"

    def summary(self):
        return "Merge runs and clean the sample logs."

    def PyInit(self):
        """ Declare properties
        """
        self.declareProperty("InputWorkspaces","", validator=StringMandatoryValidator(), doc="Comma separated list of workspaces to use, group workspaces will automatically include all members.")
        self.declareProperty(WorkspaceProperty("OutputWorkspace", "", direction=Direction.Output), doc="Name of the workspace that will contain the merged workspaces with a clean sample logs.")

        return


    def PyExec(self):
        """ Main execution body
        """
        # get parameter values
        wsInputList = [x.strip() for x in self.getPropertyValue("InputWorkspaces").split(",") ]
        wsOutput = self.getPropertyValue("OutputWorkspace")
        
        #get the workspace list
        wsNames = []
        for wsName in wsInputList: 
            #check the ws is in mantid
            ws = mtd[wsName.strip()]
            #if we cannot find the ws then stop
            if ws == None:
                raise RuntimeError ("Cannot find workspace '" + wsName.strip() + "', aborting")
            else:
                #if files are not from TOFTOF then stop
                if (ws.getInstrument().getName() != 'TOFTOF'):
                    raise ValueError('Wrong instrument')
            if isinstance(ws, WorkspaceGroup):
                wsNames.extend(ws.getNames())
            else:
                wsNames.append(wsName)

        list_SampleLogs =[]   
        for i in range(len(wsNames)):
            list_SampleLogs.append([])
            wsName= wsNames[i]
            ws = mtd[wsName]
            run=ws.getRun()
            logs = run.getLogData()
            DATA={}
            for j in range(len(logs)):
                entry=logs[j].name
                value=logs[j].value
                DATA[entry]=value
            list_SampleLogs[i]=DATA
            
        if mtd.doesExist(wsOutput):
            DeleteWorkspace(Workspace=wsOutput)

        wsOutput= MergeRuns(wsNames)
        run=wsOutput.getRun()
        logs = run.getLogData()
        DATAOut={}
        for j in range(len(logs)):
            entry=logs[j].name
            value=logs[j].value
            DATAOut[entry]=value

        list_identical=['wavelength', 'run_title', 'chopper_speed','chopper_ratio',\
        'channel_width','proposal_title','proposal_number','experiment_team','Ei','EPP','mode' ]
        for entry in list_identical:
            a=[list_SampleLogs[k][entry] for k in range(len(wsNames))]
            
            if (a.count(DATAOut[entry]) != len(wsNames)):
                 raise RuntimeError(entry + " is different between files to be merged', aborting")
           
        #Values in Sample Logs to be averaged: temperature
        avgtemp=1./len(wsNames)*sum([float(list_SampleLogs[k]['temperature']) for k in range(len(wsNames))])
        AddSampleLog(Workspace='wsOutput',LogName='temperature',LogText=str(avgtemp),LogType='Number')
      
        # Values in Sample Logs - Min and Max
        #duration - min
        min_duration=min([list_SampleLogs[k]['duration'] for k in range(len(wsNames))])
        AddSampleLog(Workspace='wsOutput',LogName='duration',LogText=min_duration,LogType='Number')
        
        #run_start - min
        min_rstart=min([list_SampleLogs[k]['run_start'] for k in range(len(wsNames))])
        AddSampleLog(Workspace='wsOutput',LogName='run_start',LogText=min_rstart,LogType='String')
        
        #run_end - max
        max_rend=max([list_SampleLogs[k]['run_end'] for k in range(len(wsNames))])
        AddSampleLog(Workspace='wsOutput',LogName='run_end',LogText=max_rend,LogType='String')
        
        #full_channels - min
        min_fchannels=min([list_SampleLogs[k]['full_channels'] for k in range(len(wsNames))])
        AddSampleLog(Workspace='wsOutput',LogName='full_channels',LogText=str(min_fchannels),LogType='Number')
        
        # Values in Sample Logs to be listed: run_number
        lrun_nb=[list_SampleLogs[k]['run_number'] for k in range(len(wsNames))]
        AddSampleLog(Workspace='wsOutput',LogName='run_number',LogText=str(lrun_nb),LogType='String')
        
        # Values in Sample Logs to be added
        mcounts = sum([int(list_SampleLogs[k]['monitor_counts']) for k in range(len(wsNames))])
        AddSampleLog(Workspace='wsOutput',LogName='monitor_counts',LogText=str(mcounts),LogType='Number')
        
        self.setProperty("OutputWorkspace",wsOutput)
        
#########################################################################################
# Registration
AlgorithmFactory.subscribe(CleanSampleLogs)




