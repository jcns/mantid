from __future__ import (absolute_import, division, print_function)

from mantid.api import PythonAlgorithm, AlgorithmFactory, mtd
from mantid.kernel import Direction

import numpy as np


class DNSProcessStandardData(PythonAlgorithm):
    """
    sort sample and background workspaces to table
    """

    def category(self):
        return "Workflow\\MLZ\\DNS"

    def PyInit(self):

        self.declareProperty(name="SampleTable",     defaultValue="", doc="Table of sample Data")
        self.declareProperty(name="BackgroundTable", defaultValue="", doc="Table of background Data")
        self.declareProperty(name="OutputWorkspace", defaultValue="", doc="Name of the output workspace")
        self.declareProperty(name="OutputTable",     defaultValue="", doc="Name of the output table")
        self.declareProperty(name="Polarisations",   defaultValue="", direction=Direction.Output,
                             doc="List of polarisations in the data")

    def PyExec(self):

        # list of workspace types
        ws_types = []

        # name and group name of the ws columns
        column_names      = {}
        column_group_name = {}

        sample_table = mtd[self.getProperty("SampleTable").value]
        leer_name    = self.getProperty("BackgroundTable").value

        output_ws_name = self.getProperty("OutputWorkspace").value
        out_table_name = output_ws_name+"_"+self.getProperty("OutputTable").value

        table_ws = sample_table.clone(OutputWorkspace=out_table_name)

        # if background needed (not if no correction)
        if mtd.doesExist(leer_name):
            leer = mtd[leer_name]
            ws_types.append(leer)
            column_names[leer.getName()]      = "background_ws"
            column_group_name[leer.getName()] = "background_group_ws"

            # new columns for background data
            table_ws.addColumn("str", "background_ws")
            table_ws.addColumn("str", "background_group_ws")

        polarisations_list = []

        # sort background workspaces to data workspaces with same polarisation, filpp and deterota
        for i in range(table_ws.rowCount()):
            row_out = table_ws.row(i)
            for t in ws_types:
                for j in range(t.rowCount()):
                    row = t.row(j)
                    pol = row_out["polarisation"]
                    if pol == row["polarisation"]:
                        if pol not in polarisations_list:
                            polarisations_list.append(pol)
                        if row_out["flipper"] == row["flipper"]:
                            if np.abs(float(row_out["deterota"]) - float(row["deterota"])) < 0.5:
                                table_ws.setCell(column_names[t.getName()], i, row["run_title"])
                                table_ws.setCell(column_group_name[t.getName()], i, row["ws_group"])
        polarisations = ", ".join(polarisations_list)

        self.setProperty("Polarisations", polarisations)

AlgorithmFactory.subscribe(DNSProcessStandardData)
