.. algorithm::

.. summary::

.. alias::

.. properties::

Description
-----------

Converts a workspace data into several ASCII files. 

-  In the files the data are stored in columns: the first column contains the energy-values, followed by the intensity and its error values. The last column correspond to the momentum transfer :math:`Q`. 

-  The number of files generated depends on the number of :math:`Q`-values contained in the input workspace.  One file is associated with one value of :math:`Q`.

- By default existing output files will be overwritten. If OverwriteExistingFiles is set to 'False', the existing filenames will be appended with the actual date and time. 

- The default extension is '.txt'. Users can choose between '.dat' and '.txt' 



Restriction on the input workspace
###################################

-  The intensity of the input workspace must be as a function of **momentum transfer** :math:`Q` and **energy transfer** :math:`\Delta E`.


Usage
-----

**Example**

.. testcode:: ExTOFTOFSaveAscii

    # Generation of a workspace with the correct units using TOFTOF's IDF 
    idf = os.path.join(config['instrumentDefinition.directory'], "TOFTOF_Definition.xml")
    ws = LoadEmptyInstrument(Filename=idf)
    ws = CropWorkspace(ws, EndWorkspaceIndex=10)
    ws.getAxis(0).setUnit('DeltaE')
    ws.getAxis(1).setUnit('MomentumTransfer')

    TOFTOFSaveAscii(InputWorkspace=ws,OutputFilename='test',Extension=".txt")
    # generates testws_0.txt,..., testws_10.txt in your Default Save Directory

    print "Unit of X-axis of input workspace: ", ws.getAxis(0).getUnit().unitID()
    print "Unit of Y-axis of input workspace:", ws.getAxis(1).getUnit().unitID()
    print "Workspace size = (", ws.getNumberHistograms(), ",", ws.blocksize(), ")"
    print "Creation of {} files containing {} lines with DeltaE, intensity, error, and momentum transfer.".format(ws.getNumberHistograms(),ws.blocksize())

    # Check contents of generated files
    output_dir = config['defaultsave.directory']
    for i in range(ws.getNumberHistograms()):
        filename = output_dir + 'testws_%d.txt'%i
        f = open(filename, 'r')
        print ('Content of file test_%d.txt: ')%i
        for line in f:
            print line
        f.close()


   
    

Output:

.. testoutput:: ExTOFTOFSaveAscii

    Unit of X-axis of input workspace:  DeltaE
    Unit of Y-axis of input workspace: MomentumTransfer
    Workspace size = ( 11 , 1 )
    Creation of 11 files containing 1 lines with DeltaE, intensity, error, and momentum transfer.
    Content of file test_0.txt: 
    0.0	1.0	1.0	1.0

    Content of file test_1.txt: 
    0.0	1.0	1.0	2.0

    Content of file test_2.txt: 
    0.0	1.0	1.0	3.0

    Content of file test_3.txt: 
    0.0	1.0	1.0	4.0

    Content of file test_4.txt: 
    0.0	1.0	1.0	5.0

    Content of file test_5.txt: 
    0.0	1.0	1.0	6.0

    Content of file test_6.txt: 
    0.0	1.0	1.0	7.0

     Content of file test_7.txt: 
     0.0	1.0	1.0	8.0

     Content of file test_8.txt: 
     0.0	1.0	1.0	9.0

     Content of file test_9.txt: 
     0.0	1.0	1.0	10.0

     Content of file test_10.txt: 
    0.0	1.0	1.0	11.0

    
.. categories::

.. sourcelink::
