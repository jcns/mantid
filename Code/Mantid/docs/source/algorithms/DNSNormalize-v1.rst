.. algorithm::

.. summary::

.. alias::

.. properties::

Description
-----------

This algorithm is a part of the DNS data reduction workflow. It normalizes the given :ref:`Workspace2D <Workspace2D>` by the given log value. For the moment, only normalization by duration and by monitor is supported. Since for DNS only a single value for monitor counts and for run duration is provided, the :ref:`algm-Scale` algorithm is used to divide the data by this value. The normalisation scheme used is:

:math:`(s_i)_{Norm}=\frac{s_i}{m}`

where :math:`s_i` is the signal for detector :math:`i` and :math:`m` is either monitor counts or run duration value. 

.. warning::

    Since the data reduction workflow for DNS instrument is getting established for the moment, this algorithm may change in the near future.

Usage
-----

**Example - Load a DNS legacy file and normalize by duration**

.. testcode:: exDNSNormalizeByDuration

   # data file.
   datafile = 'dn134011vana.d_dat'

   # Load dataset
   ws = LoadDNSLegacy(datafile, Polarisation='x')

   # View the duration
   run = ws.getRun()
   print "Run duration is", run.getProperty('duration').value, "seconds."

   # Normalize workspace ws by duration
   wsnorm = DNSNormalize(ws, NormalizeBy='duration')
   print "First 3 values of " + ws.getName()
   print ws.readY(0), ws.readY(1), ws.readY(2)

   print "First 3 values of " + wsnorm.getName()
   print wsnorm.readY(0), wsnorm.readY(1), wsnorm.readY(2)

Output:

.. testoutput:: exDNSNormalizeByDuration

   Run duration is 600.0 seconds.
   First 3 values of ws
   [ 4366.] [ 31461.] [ 33314.]
   First 3 values of wsnorm
   [ 7.27666667] [ 52.435] [ 55.52333333]

.. categories::
