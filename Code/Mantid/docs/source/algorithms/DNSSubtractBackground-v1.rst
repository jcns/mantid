.. algorithm::

.. summary::

.. alias::

.. properties::

Description
-----------

This algorithm is a part of the DNS data reduction workflow. It subtracts the given background :ref:`Workspace2D <Workspace2D>` from the given data :ref:`Workspace2D <Workspace2D>`. Before subtraction, both data and background workspaces are normalized by the given log value using the :ref:`algm-DNSNormalize` algorithm. **Important: the OutputWorkspace will contain normalized data.** 

This algorithms also checks whether data and background workspaces have the same values for the following sample logs: *slit_i_upper_blade_position*, *slit_i_lower_blade_position*, *slit_i_left_blade_position*, *slit_i_right_blade_position*, *flipper*, *deterota*, *polarisation*. If some of these logs are different, warning is produced. The OutputWorkspace will have the sample logs identical to the DataWorkspace. If some of these logs are absent either in DataWorkspace or in BackgroundWorkspace, the checking is not performed and warning is produced. 

.. warning::

    Since the data reduction workflow for DNS instrument is getting established for the moment, this algorithm may change in the near future.

Usage
-----

**Example - Load a DNS legacy file and suctract the background**

.. testcode:: exDNSSubtractBackground

   # data file.
   datafile = 'dn134011vana.d_dat'
   bkgfile = 'dn134031leer.d_dat'

   # Load datasets
   data_ws = LoadDNSLegacy(datafile, Polarisation='x')
   bkg_ws = LoadDNSLegacy(bkgfile, Polarisation='x')

   # Subtract the background
   data = DNSSubtractBackground(data_ws, bkg_ws, NormalizeBy='duration')
   print "First 3 values of " + data_ws.getName()
   print data_ws.readY(0), data_ws.readY(1), data_ws.readY(2)

   print "First 3 values of " + data.getName()
   print data.readY(0), data.readY(1), data.readY(2)

Output:

.. testoutput:: exDNSSubtractBackground

   First 3 values of data_ws
   [ 4366.] [ 31461.] [ 33314.]
   First 3 values of data
   [ 4.29333333] [ 46.73766667] [ 51.40933333]

.. categories::
