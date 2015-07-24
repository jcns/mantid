.. algorithm::

.. summary::

.. alias::

.. properties::

Description
-----------

Converts the units of :

- the X values of a :ref:`workspace <Workspace>` from time of flight to energy transfer :math:`\Delta E` (in meV), 

The energy transfer is calculated as: :math:`\Delta E = \frac{m_n L_{sd}^2}{2} \left ( \frac{1}{tof_{elastic}^2} - \frac{1}{t^2}\right )`, where 
:math:`m_n` is the neutron mass
:math:`L_{sd}` the distance sample-detector (*i.e.* the length of the secondary detector)

- the Y values are normalized and the conversion to energy is also taken into account. Therefore the intensity is corrected by the term :math:`\frac{m_n L_{sd}^2 t^3}{\Delta t}`, where :math:`\Delta t` is the channel width,

- the E values are corrected accordingly.


To date this algorithm only supports the TOFTOF instrument.


There are three options to calculate the elastic line :math:`tof_{elastic}^2` using the value contained in the input SampleLogs or from a Gaussian fit of the sample data or from a Gaussian fit of some vanadium workspace.


Usage
-----

**Example**

.. testcode:: ExTOFTOFConvertTofToDeltaE

    # Load sample data
    wsSample=LoadMLZ(Filename='TOFTOFTestdata.nxs')
    
    # First option: Elastic line from the sample data (guessed value) - Default
    wsOutGuess=TOFTOFConvertTofToDeltaE(wsSample)
    # Third option: Elastic line from fit of Sample data
    wsOutFitSample=TOFTOFConvertTofToDeltaE(wsSample,ChoiceElasticTof='FitSample')

    print "Unit of X-axis before conversion: ", wsSample.getAxis(0).getUnit().unitID()

    print "Unit of X-axis after conversion: ",  wsOutGuess.getAxis(0).getUnit().unitID(), wsOutFitSample.getAxis(0).getUnit().unitID()

  

Output:

.. testoutput:: ExTOFTOFConvertTofToDeltaE

   Unit of X-axis before conversion:  TOF
   Unit of X-axis after conversion:  DeltaE DeltaE

.. categories::

.. sourcelink::
