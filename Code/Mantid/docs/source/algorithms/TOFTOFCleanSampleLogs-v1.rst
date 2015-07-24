.. algorithm::

.. summary::

.. alias::

.. properties::

Description
-----------

Corrects the SampleLogs of a Merged Workspace.

To date this algorithm only supports the TOFTOF instrument.

The SampleLogs from TOFTOF files contain data used for further reduction. 

The values from different merged workspaces are set into the final workspace in the following way:


+---------++-------------------------------+
| Type of || Parameter                     |
| merging ||                               |
+=========++===============================+
| Average || temperature                   |
+---------++-------------------------------+
| Minimum || run_start, full time_channels |
+---------++-------------------------------+
| Maximum || run_end                       |
+---------++-------------------------------+
| Summed  || duration, monitor_counts      |
+---------++-------------------------------+
| Listed  || run_number                    |
+---------++-------------------------------+

Usage
-----

**Example - Clean Sample Logs from list of workspaces**

.. testcode:: ExTOFTOFCleanSampleLogs2ws

    ws1 = LoadMLZ(Filename='TOFTOFTestdata.nxs')
    ws2 = LoadMLZ(Filename='TOFTOFTestdata1.nxs')

    # Input = list of workspaces
    ws3 = TOFTOFCleanSampleLogs('ws1,ws2')

    # Temperature 
    print "Temperature of experiment for 1st workspace (in K): ", mtd['ws1'].getRun().getLogData('temperature').value
    print "Temperature of experiment for 2nd workspace (in K): ", mtd['ws2'].getRun().getLogData('temperature').value
    print "Temperature of experiment for merged workspaces = average over workspaces (in K): ",  mtd['ws3'].getRun().getLogData('temperature').value

    # Duration
    print "Duration of experiment for 1st workspace (in s): ",  mtd['ws1'].getRun().getLogData('duration').value
    print "Duration of experiment for 2nd workspace (in s): ",  mtd['ws2'].getRun().getLogData('duration').value
    print "Duration of experiment for merged workspaces = sum of all durations (in s): ",  mtd['ws3'].getRun().getLogData('duration').value

    # Run start 
    print "Start of experiment for 1st workspace: ",  mtd['ws1'].getRun().getLogData('run_start').value
    print "Start of experiment for 2nd workspace: ",  mtd['ws2'].getRun().getLogData('run_start').value
    print "Start of experiment for merged workspaces = miminum of all workspaces: ",  mtd['ws3'].getRun().getLogData('run_start').value

    # Run end 
    print "End of experiment for 1st workspace: ",  mtd['ws1'].getRun().getLogData('run_end').value
    print "End of experiment for 2nd workspace: ",  mtd['ws2'].getRun().getLogData('run_end').value
    print "End of experiment for merged workspaces = maximum of all workspaces: ",  mtd['ws3'].getRun().getLogData('run_end').value

    # Full channels 
    print "Number of full time channels for 1st workspace: ",  mtd['ws1'].getRun().getLogData('full_channels').value
    print "Number of full time channels for 2nd workspace: ",  mtd['ws2'].getRun().getLogData('full_channels').value
    print "Number of full time channels for merged workspaces = minimum of all workspaces: ",  mtd['ws3'].getRun().getLogData('full_channels').value
    
    # Run number 
    print "Run number for 1st workspace: ",  mtd['ws1'].getRun().getLogData('run_number').value
    print "Run number for 2nd workspace: ",  mtd['ws2'].getRun().getLogData('run_number').value
    print "Run number for merged workspaces = list of all workspaces: ",  mtd['ws3'].getRun().getLogData('run_number').value      
 
    # Monitor counts
    print "Monitor counts for 1st workspace: ",  mtd['ws1'].getRun().getLogData('monitor_counts').value
    print "Monitor counts for 2nd workspace: ",  mtd['ws2'].getRun().getLogData('monitor_counts').value
    print "Monitor counts for merged workspaces = sum over all workspaces: ",  mtd['ws3'].getRun().getLogData('monitor_counts').value      
   

Output:

.. testoutput:: ExTOFTOFCleanSampleLogs2ws

    Temperature of experiment for 1st workspace (in K):  294.149414
    Temperature of experiment for 2nd workspace (in K):  294.150696
    Temperature of experiment for merged workspaces = average over workspaces (in K):  294.150055
    Duration of experiment for 1st workspace (in s):  3601
    Duration of experiment for 2nd workspace (in s):  3600
    Duration of experiment for merged workspaces = sum of all durations (in s):  7201.0
    Start of experiment for 1st workspace:  2013-07-28T10:32:19+0100
    Start of experiment for 2nd workspace:  2013-07-28T11:32:21+0100
    Start of experiment for merged workspaces = miminum of all workspaces:   2013-07-28T10:32:19+0100
    End of experiment for 1st workspace:  2013-07-28T11:32:20+0100
    End of experiment for 2nd workspace:  2013-07-28T12:32:21+0100
    End of experiment for merged workspaces = maximum of all workspaces:  2013-07-28T12:32:21+0100
    Number of full time channels for 1st workspace:  1020.0
    Number of full time channels for 2nd workspace:  1020.0
    Number of full time channels for merged workspaces = minimum of all workspaces:  1020.0
    Run number for 1st workspace:  TOFTOFTestdata
    Run number for 2nd workspace:  TOFTOFTestdata1
    Run number for merged workspaces = list of all workspaces:  ['TOFTOFTestdata', 'TOFTOFTestdata 1']
    Monitor counts for 1st workspace:  136935
    Monitor counts for 2nd workspace:  137307
    Monitor counts for merged workspaces = sum over all workspaces:  274242

**Example - Clean Sample Logs from group of workspaces**

.. testcode:: ExTOFTOFCleanSampleLogsGroup

    group=GroupWorkspaces('ws1,ws2')
    groupclean=TOFTOFCleanSampleLogs(group)
    print "Monitor counts for 1st workspace: ",  mtd['ws1'].getRun().getLogData('monitor_counts').value
    print "Monitor counts for 2nd workspace: ",  mtd['ws2'].getRun().getLogData('monitor_counts').value
    print "Monitor counts for merged workspaces = sum over all workspaces: ",  mtd['groupclean'].getRun().getLogData('monitor_counts').value         

Output:

.. testoutput:: ExTOFTOFCleanSampleLogsGroup

    Monitor counts for 1st workspace:  136935
    Monitor counts for 2nd workspace:  137307
    Monitor counts for merged workspaces = sum over all workspaces:  274242

.. categories::

.. sourcelink::

  

