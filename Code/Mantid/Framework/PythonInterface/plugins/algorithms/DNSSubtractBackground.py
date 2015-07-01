import mantid.simpleapi as api
from mantid.api import PythonAlgorithm, AlgorithmFactory, WorkspaceProperty, mtd
from mantid.kernel import Direction, StringListValidator


NORMALIZATIONS = ['duration', 'mon_sum']


class DNSSubtractBackground(PythonAlgorithm):
    """
    Subtracts the given background workspace from the data workspace.
    This algorithm is developed for the DNS @ MLZ,
    but can be used for other instruments if appropriate.
    """
    def category(self):
        """
        Returns category
        """
        return 'PythonAlgorithms\\MLZ\\DNS\\NormalisationCorrections'

    def name(self):
        """
        Returns name
        """
        return "DNSSubtractBackground"

    def summary(self):
        return "Subtracts the given background workspace from the data workspace. \
                This algorithm is developed for DNS @ MLZ, \
                but can be used for other instruments if appropriate."

    def PyInit(self):
        self.declareProperty(WorkspaceProperty("DataWorkspace",
                                               "", direction=Direction.Input),
                             doc="A workspace with experimental data.")
        self.declareProperty(WorkspaceProperty("BackgroundWorkspace",
                                               "", direction=Direction.Input),
                             doc="A workspace with background data.")
        self.declareProperty(WorkspaceProperty("OutputWorkspace",
                                               "", direction=Direction.Output),
                             doc="A workspace to save the result.")
        self.declareProperty(name="NormalizeBy", defaultValue='duration',
                             validator=StringListValidator(NORMALIZATIONS),
                             doc="Name of the log value to normalize by. \
                             Valid values: %s" % str(NORMALIZATIONS))
        return

    def PyExec(self):
        # Input
        dataws = mtd[self.getPropertyValue("DataWorkspace")]
        bkgws = mtd[self.getPropertyValue("BackgroundWorkspace")]
        outws = self.getPropertyValue("OutputWorkspace")
        norm = self.getPropertyValue("NormalizeBy")

        data_run = dataws.getRun()
        bkg_run = bkgws.getRun()
        # check whether sample logs contain necessary stuff
        logs_needed = sorted(['slit_i_upper_blade_position', 'slit_i_lower_blade_position',
                              'slit_i_left_blade_position', 'slit_i_right_blade_position',
                              'flipper', 'deterota', 'polarisation'])

        intersect1 = sorted(list(set(data_run.keys()) & set(logs_needed)))
        intersect2 = sorted(list(set(bkg_run.keys()) & set(logs_needed)))
        if intersect1 != logs_needed:
            self.log().warning('Workspace %s does not contain DNS sample logs!' % dataws.getName())
        elif intersect2 != logs_needed:
            self.log().warning('Workspace %s does not contain DNS sample logs!' % bkgws.getName())
        else:
            # check slits and produce warning if different
            # create a list of slit blades [upper, lower, left, right]
            data_slits = [data_run.getProperty('slit_i_upper_blade_position').value,
                          data_run.getProperty('slit_i_lower_blade_position').value,
                          data_run.getProperty('slit_i_left_blade_position').value,
                          data_run.getProperty('slit_i_right_blade_position').value]
            bkg_slits = [bkg_run.getProperty('slit_i_upper_blade_position').value,
                         bkg_run.getProperty('slit_i_lower_blade_position').value,
                         bkg_run.getProperty('slit_i_left_blade_position').value,
                         bkg_run.getProperty('slit_i_right_blade_position').value]
            if cmp(data_slits, bkg_slits):
                self.log().warning('You subtract workspaces with different slit blades positions! \
                                   \n Slit blades position for the workspaces are [upper, lower, left, right]: \
                                   \n Workspace ' + dataws.getName() + str(data_slits) +
                                   '.\n Workspace ' + bkgws.getName() + str(bkg_slits))

            # check flipper status and produce warning if different
            data_f = data_run.getProperty('flipper').value
            bkg_f = bkg_run.getProperty('flipper').value
            if data_f != bkg_f:
                self.log().warning('You subtract workspaces with different flipper status! \
                                   \n Workspace %s has flipper %s, but workspace %s %s!'
                                   % (dataws.getName(), data_f, bkgws.getName(), bkg_f))

            # check detector position and produce warning if different
            data_det = float(data_run.getProperty('deterota').value)
            bkg_det = float(bkg_run.getProperty('deterota').value)
            tolerance = 0.01
            if abs(data_det - bkg_det) > tolerance:
                self.log().warning('You subtract workspaces with different detector bank positions! \
                                   \n Workspace %s has position %f, but workspace %s %f!'
                                   % (dataws.getName(), data_det, bkgws.getName(), bkg_det))

            # check polarization and produce warning if different
            data_pol = data_run.getProperty('polarisation').value
            bkg_pol = bkg_run.getProperty('polarisation').value
            if data_pol != bkg_pol:
                self.log().warning('You subtract workspaces with different polarisations! \
                                   \n Workspace %s has polarisation %s, but workspace %s %s!'
                                   % (dataws.getName(), data_pol, bkgws.getName(), bkg_pol))

        # normalize the data and the background
        __data_norm__ = api.DNSNormalize(dataws, NormalizeBy=norm)
        __bkg_norm__ = api.DNSNormalize(bkgws, NormalizeBy=norm)

        __substracted__ = __data_norm__ - __bkg_norm__

        self.setProperty("OutputWorkspace", __substracted__)
        self.log().debug('DNSSubtractBackground has saved the result to ' + outws)
        api.DeleteWorkspace(__substracted__)
        api.DeleteWorkspace(__bkg_norm__)
        api.DeleteWorkspace(__data_norm__)

        return

# Register algorithm with Mantid
AlgorithmFactory.subscribe(DNSSubtractBackground)
