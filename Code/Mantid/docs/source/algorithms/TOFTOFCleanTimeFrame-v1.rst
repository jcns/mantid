.. algorithm::

.. summary::

.. alias::

.. properties::

Description
-----------

Calculates the boundaries of full time channels for a workspace or a group of workspaces. These boundaries are then used as inputs with the algorithm
:ref:`algm-Cropworkspace` 


To date this algorithm only supports the TOFTOF instrument.



Restriction on the input workspace
###################################

-  The unit of the X-axis has to be **time-of-flight**.


Usage
-----

**Example**

.. testcode:: ExTOFTOFCleanTimeFrame

    # Load data
    ws=Load(Filename='TOFTOFTestdata.nxs')

    print "Input workspace"
    print "Total number of time channels: ",  len(ws.readX(0))
    print  "Number of filled time channels: ", ws.getRun().getLogData('full_channels').value

    wscropped = TOFTOFCleanTimeFrame(ws)

    print "Output workspace"
    print "Total number of time channels: ",  len(wscropped.readX(0))    

Output:

.. testoutput:: ExTOFTOFCleanTimeFrame
    Input workspace
    Total number of time channels:  1025
    Number of filled time channels:  1020.0
    Output workspace
    Total number of time channels:  1020
    

    
.. categories::

.. sourcelink::
