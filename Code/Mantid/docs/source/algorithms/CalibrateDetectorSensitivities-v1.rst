.. algorithm::

.. summary::

.. alias::

.. properties::

Description
-----------

Generates a workspace of Vanadium data for further normalization.

This algorithm uses a Gaussian fit for each spectrum. The Vanadium
counts are then summed within the range max_peak :math:`\pm` 3
fwhm_peak. 

The Debye Waller factor is corrected following the method described in Sears and Shelley *Acta Cryst. A* **47**, 441 (1991).

If no temperature is defined in the input workspace, the room
temperature is used.

The ouput workspace can be used as a RHS workspace in
:ref:`algm-Divide` to normalize the LHS workspace by Vanadium.

Each spectrum is filled with the normalization coefficient.

To date this algorithm only supports the TOFTOF instrument.



Restriction on the input workspace
###################################

The input workspace must contain Vanadium's data.


Usage
-----

**Example**

.. testcode:: ExCalibrateDetectorsSensitivities

    import numpy as np
    # Load Vanadium data
    wsVana = LoadMLZ(Filename='TOFTOFTestdata.nxs')
    print 'The input workspace must contain Vanadium data:', mtd['wsVana'].getRun().getLogData('run_title').value
    wsVanaout = CalibrateDetectorSensitivities(wsVana)
    print 'Spectrum 4 of the output workspace is filled with: ', wsVanaout.readY(4)
    # wsVanaout to be used as rhs with Divide algorithm in order to normalize data

Output:    

.. testoutput:: ExCalibrateDetectorsSensitivities

    The input workspace must contain Vanadium data: Vanadium
    Spectrum 4 of the output workspace is filled with:  [ 5641.96849424  5641.96849424  5641.96849424 ...,  5641.96849424
  5641.96849424  5641.96849424]

.. categories::

.. sourcelink::
