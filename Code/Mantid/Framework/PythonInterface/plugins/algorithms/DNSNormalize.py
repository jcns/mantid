import mantid.simpleapi as api
from mantid.api import PythonAlgorithm, AlgorithmFactory, WorkspaceProperty, mtd
from mantid.kernel import Direction, StringListValidator


NORMALIZATIONS = ['duration', 'mon_sum']


class DNSNormalize(PythonAlgorithm):
    """
    Normalizes the given matrix workspace by the given log value.
    Normalization either to monitor or to duration is supported for the moment.
    This algorithm is written for the DNS @ MLZ,
    but can be used for other instruments if needed.
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
        return "DNSNormalize"

    def summary(self):
        return "Normalizes the given matrix workspace by the given log value. \
                Normalization either by monitor or by duration is supported \
                for the moment. This algorithm is developed for DNS @ MLZ, \
                but can be used for other instruments if needed."

    def PyInit(self):
        self.declareProperty(WorkspaceProperty("InputWorkspace",
                                               "", direction=Direction.Input),
                             doc="A workspace with raw experimental data.")
        self.declareProperty(WorkspaceProperty("OutputWorkspace",
                                               "", direction=Direction.Output),
                             doc="A workspace to save the normalized data.")
        self.declareProperty(name="NormalizeBy", defaultValue='duration',
                             validator=StringListValidator(NORMALIZATIONS),
                             doc="Name of the log value to normalize by. \
                             Valid values: %s" % str(NORMALIZATIONS))
        return

    def PyExec(self):
        # Input
        dataws = mtd[self.getPropertyValue("InputWorkspace")]
        # outws = self.getPropertyValue("OutputWorkspace")
        norm = self.getPropertyValue("NormalizeBy")
        run = dataws.getRun()
        try:
            nvalue = run.getProperty(norm).value
        except:
            raise ValueError("The normalization parameter %s is not valid" % norm)
        else:
            __scaled_data__ = api.Scale(dataws, 1.0/nvalue, "Multiply")

            self.setProperty("OutputWorkspace", __scaled_data__)
            self.log().debug('DNS data have been normalized by %s=%d.' % (norm, nvalue))
            api.DeleteWorkspace(__scaled_data__)

        return

# Register algorithm with Mantid
AlgorithmFactory.subscribe(DNSNormalize)
