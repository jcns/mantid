#pylint: disable=no-init
import mantid.simpleapi as api
from mantid.api import *
from mantid.kernel import *
from mantid import config

DEFAULT_BINS = [0., 0., 0.]

class TOFTOFReduction(PythonAlgorithm):
    def category(self):
        return "Inelastic;PythonAlgorithms"

    def name(self):
        return "TOFTOFReduction"

    def summary(self):
        return "This algorithm is meant to reduce TOFTOF's data via Mantid."

    def PyInit(self):
        self.declareProperty("Sample data", "", validator=StringMandatoryValidator(),
                             doc='Sample - Input files or workspaces to load')

        self.declareProperty("Vanadium data", "", doc='Vanadium - Input files or workspaces to load')

        # Empty cans
        # self.declareProperty("Use Empty cans data", False, direction=Direction.Input,
        #                     doc="Use Empty cans data in the reduction.")

        self.declareProperty("Empty cans data for Sample", "",
                             doc="Empty cans data for Sample - Input files or workspaces to load")

        # Optional empty cans - by default we use the same EC for Sample and Vanadium data
        self.declareProperty("Empty cans data for Vanadium", "",
                             doc="Empty cans data for Vanadium - Input files or workspaces to load")

        # Apply masks
        self.declareProperty("Mask detectors", False, """Launch diagnostic to mask faulty detectors: outside of some
        given angular ranges, selected as faulty.""")

        self.declareProperty("Mask by Ids", "", direction=Direction.Input,
                             doc="List of detectors to be masked")

        self.declareProperty("Mask by Angles", "", direction=Direction.Input,
                             doc="Intervals of angles to mask detectors. Semicolons delimit the intervals.")

        # Normalization
        # to monitor counts
        self.declareProperty("Normalize to Monitor counts", False)
        # to EC
        self.declareProperty("Normalize to Empty cans", False, direction=Direction.Input, doc="Normalize to Empty cans")
        # to Vanadium
        self.declareProperty("Normalize to Vanadium", False, direction=Direction.Input,
                             doc="Normalize to Vanadium data")
        # scale
        self.declareProperty("Scale factor to Empty cans data", 1.,
                             "Apply this transmission factor to the Empty cans workspaces")

        # Crop time channels
        self.declareProperty("Clean Time Channels", False, direction=Direction.Input,
                             doc="Crop incomplete time channels")

        # Conversion
        self.declareProperty("Convert tof to DeltaE", False, direction=Direction.Input,
                             doc="Convert time of flight to energy transfer in sample data runs.")

        choice_tof = ["Geometry", "FitVanadium", "FitSample"]
        self.declareProperty("ChoiceElasticTof", "Geometry", StringListValidator(choice_tof), direction=Direction.Input,
                             doc="Method to determine the elastic line")

        # Detector efficiency cor user tick
        self.declareProperty("Correct Sample data for detector efficiency", False, direction=Direction.Input,
                             doc="Correct Sample and Vanadium data for the energy dependent detector efficiency.")

        self.declareProperty("Apply Ki/Kf correction", False, direction=Direction.Input,
                             doc="Apply Ki/Kf correction to Sample and Vanadium data.")

        self.declareProperty("Rebin the data", False, direction=Direction.Input,
                             doc='Apply rebin to Sample and Vanadium data.')

        self.declareProperty(FloatArrayProperty("EnergyBins", DEFAULT_BINS, direction=Direction.Input),
                             doc="Energy transfer binning scheme (in ueV)")

        self.declareProperty("Calculate S(Q, Omega)", False, direction=Direction.Input,
                             doc="Apply algorithm SofQW to Sample and Vanadium data.")

        self.declareProperty(FloatArrayProperty("MomentumTransferBins", DEFAULT_BINS, direction=Direction.Input),
                             doc="Momentum transfer binning scheme")

        # Generate output files
        self.declareProperty("Save Ascii", False, direction=Direction.Input, doc="Save data as Ascii files")
        # Name output files -
        self.declareProperty(FileProperty("Outputfile Prefix", "outputASCII", FileAction.OptionalSave),
                             doc="Output files of the workspace - split according to q-values.")

        extensions = [".txt", ".dat"]
        self.declareProperty("Outputfile Extension", ".txt", StringListValidator(extensions),
                             doc="Extension of the output files.")

        self.declareProperty("Overwrite existing ASCII output files", True,
                             doc="Overwrite existing files. If false, the date is added to the filename.")

        # self.declareProperty("Generate intermediate output workspaces", True, direction=Direction.Input,
        #                     doc="Generate output workspaces for each algorithm.")

        # Group entries in display
        lrg = 'Input files and Merge runs'
        self.setPropertyGroup("Sample data", lrg)
        self.setPropertyGroup("Vanadium data", lrg)
        # self.setPropertyGroup("Use Empty cans data", lrg)
        self.setPropertyGroup("Empty cans data for Sample", lrg)
        # Optional: by default same as for Sample data
        self.setPropertyGroup("Empty cans data for Vanadium", lrg)

        lrg1 = 'Detector diagnostic'
        self.setPropertyGroup("Mask detectors", lrg1)
        self.setPropertyGroup("Mask by Ids", lrg1)
        self.setPropertyGroup("Mask by Angles", lrg1)

        lrg2 = "Normalization"
        self.setPropertyGroup("Scale factor to Empty cans data", lrg2)
        self.setPropertyGroup("Normalize to Monitor counts", lrg2)
        self.setPropertyGroup("Normalize to Empty cans", lrg2)
        self.setPropertyGroup("Normalize to Vanadium", lrg2)

        lrg3 = "Time correction"
        self.setPropertyGroup("Clean Time Channels", lrg3)

        lrg4 = 'Conversions'
        self.setPropertyGroup("Convert tof to DeltaE", lrg4)
        self.setPropertyGroup("ChoiceElasticTof", lrg4)
        self.setPropertyGroup("Correct Sample data for detector efficiency", lrg4)
        self.setPropertyGroup("Apply Ki/Kf correction", lrg4)
        self.setPropertyGroup("Rebin the data", lrg4)
        self.setPropertyGroup("EnergyBins", lrg4)
        self.setPropertyGroup("Calculate S(Q, Omega)", lrg4)
        self.setPropertyGroup("MomentumTransferBins", lrg4)

        # Generate output
        lrg5 = 'Output files'
        self.setPropertyGroup("Save Ascii", lrg5)
        self.setPropertyGroup("Outputfile Prefix", lrg5)
        self.setPropertyGroup("Outputfile Extension", lrg5)
        self.setPropertyGroup("Overwrite existing ASCII output files", lrg5)

    def PyExec(self):
        """ Main Execution Body
        """
        config['default.facility'] = "MLZ"
        config['default.instrument'] = "TOFTOF"

    # Load sample data
        data_input = self.getProperty("Sample Data").value
        data_list = self._get_Sample_Runs(data_input)
        list_unchanged_ws = list()

        loaded_data = list()
        # loop over sets of data
        for i, data in enumerate(data_list):
            output_name_gp = 'data_run' + str(i)
            output_name_clean_log = 'data_gp_clean_log' + str(i)
            self._load_data(data, output_name_gp, output_name_clean_log)
            loaded_data.append(output_name_clean_log)
        nb_data_sets = len(data_list)

    # Load vanadium - optional
        vana_input = self.getProperty("Vanadium Data").value
        if vana_input != "":
            self._load_data(vana_input, 'vana_gp', 'vana_gp_clean_log')
            loaded_data.append('vana_gp_clean_log')
        nb_vana_sets = len(loaded_data) - nb_data_sets

    # Load empty cans - optional
        ec_data_input = self.getProperty("Empty cans data for Sample").value
        if ec_data_input != "":
            self._load_data(ec_data_input, 'ec_data_gp', 'ec_data_gp_clean_log')
            loaded_data.append('ec_data_gp_clean_log')
        ec_vana_input = self.getProperty("Empty cans data for Vanadium").value
        if ec_vana_input != "":
            self._load_data(ec_vana_input, 'ec_vana_gp', 'ec_vana_gp_clean_log')
            loaded_data.append('ec_vana_gp_clean_log')
        nb_ec_sets = len(loaded_data) - nb_data_sets - nb_vana_sets
    # Mask detectors - detectors with no counts are masked. Masking by angle or ids is optional
        group_loaded = api.GroupWorkspaces(loaded_data)
        self._remove_empty_detectors(group_loaded)

        if self.getProperty("Mask detectors").value is True:
            if self.getProperty("Mask by Ids").value != "":
                list_iddetectors = self.getProperty("Mask by Ids").value
                self._mask_detectors_by_id(group_loaded, list_iddetectors)
            if self.getProperty("Mask by Angles").value != "":
                range_angles = self.getProperty("Mask by Angles").value
                self._mask_detectors_by_angle(group_loaded, range_angles)

    # Normalization by monitor counts
        if self.getProperty("Normalize to Monitor counts").value is True:
            group_mon_eff = api.MonitorEfficiencyCorUser(group_loaded)
        else:
            group_mon_eff = api.CloneWorkspace(group_loaded)
            list_unchanged_ws.append('group_mon_eff')

    # Treatment by EC and Vanadium if present
        # Scale empty cans and subtract empty cans
        norm_to_ec = self.getProperty("Normalize to Empty cans").value
        if norm_to_ec is True:
            group_sample = api.GroupWorkspaces([group_mon_eff.getItem(i).getName() for i in range(nb_data_sets)])
            if nb_ec_sets == 1:
                ec_ws = group_mon_eff.getItem(nb_data_sets+nb_vana_sets)
                api.Scale(InputWorkspace=ec_ws, OutputWorkspace='EC_trans',
                          Factor=self.getProperty("Scale factor to Empty cans data").value)
                group_sample_minus_ec = api.Minus(group_sample, 'EC_trans')
            elif nb_ec_sets == 2:
                multipl_factor = self.getProperty("Scale factor to Empty cans data").value
                ec_ws = group_mon_eff.getItem(nb_data_sets + nb_vana_sets)
                api.Scale(InputWorkspace=ec_ws, OutputWorkspace='EC_trans', Factor=multipl_factor)
                group_sample_minus_ec = api.Minus(group_sample, 'EC_trans')
                # To do: add treatment of Vanadium
                ec_ws_vana = group_mon_eff.getItem(nb_data_sets+nb_vana_sets+1)
                api.Scale(InputWorkspace=ec_ws_vana, OutputWorkspace='ECVana_trans', Factor=multipl_factor)
        else:
            group_sample_minus_ec = api.GroupWorkspaces([group_mon_eff.getItem(i).getName() for i in range(nb_data_sets)])
            list_unchanged_ws.append('group_sample_minus_ec')

        # To do: add treatment of ec for vanadium
        if nb_vana_sets != 0:
            wsVana = group_mon_eff.getItem(nb_data_sets)
            # api.RenameWorkspace(Inputworkspace=wsVana, Outputworkspace='wsVana')
            group_sample_vana = api.GroupWorkspaces([group_sample_minus_ec, wsVana])
            if self.getProperty("Normalize to Vanadium").value is True:
                # wsVana = group_mon_eff.getItem(nb_data_sets)
                wsVanToNorm = api.CalibrateDetectorSensitivities(wsVana)
                # group_sample_vana = api.GroupWorkspaces([group_sample_minus_ec, wsVana])
                group_detsens = api.Divide(group_sample_vana, wsVanToNorm)
                # api.DeleteWorkspace(group_sample_vana)
            else:
                group_detsens = api.CloneWorkspace(group_sample_vana) # api.GroupWorkspaces([group_sample_minus, wsVana])
                list_unchanged_ws.append('group_detsens')
                list_unchanged_ws.append('group_sample_vana')
        else:
            group_detsens = api.CloneWorkspace(group_sample_minus_ec)
            list_unchanged_ws.append('group_detsens')

    # Clean time channels
        if self.getProperty("Clean Time Channels").value is True:
            group_clean_frame = api.TOFTOFCleanTimeFrame(group_detsens)
        else:
            group_clean_frame = api.CloneWorkspace(group_detsens)
            list_unchanged_ws.append('group_clean_frame')

    # Tof2dE
        if self.getProperty("Convert tof to DeltaE").value is True:
            choice_tof = self.getProperty("ChoiceElasticTof").value
            if choice_tof == 'FitVanadium' and nb_vana_sets != 0:
                wsVanadium = group_clean_frame.getItem(group_clean_frame.getNumberOfEntries()-1)
                group_tof2de = api.TOFTOFConvertTofToDeltaE(group_clean_frame, WorkspaceVanadium=wsVanadium,
                                                           ChoiceElasticTof=choice_tof)
                api.DeleteWorkspace(wsVanadium)
            else:
                group_tof2de = api.TOFTOFConvertTofToDeltaE(group_clean_frame, ChoiceElasticTof=choice_tof)
            # DetectorEfficiencyCorUser
            if self.getProperty("Correct Sample data for detector efficiency").value is True:
                group_deteff = api.DetectorEfficiencyCorUser(InputWorkspace=group_tof2de)
            else:
                group_deteff = api.CloneWorkspace(group_tof2de)
                list_unchanged_ws.append('group_deteff')
            # CorrectKiKf
            if self.getProperty("Apply Ki/Kf correction").value is True:
                group_kikf = api.CorrectKiKf(InputWorkspace=group_deteff)
            else:
                group_kikf = api.CloneWorkspace(group_deteff)
                list_unchanged_ws.append('group_kikf')
            # Rebin
            if self.getProperty("Rebin the data").value is True:
                group_rebin = self._rebin_group(group_kikf)
                if self.getProperty("Calculate S(Q, Omega)").value is True:
                    group_sofqw = self._sofqw_group(group_rebin)
                    # TOFTOFSaveAscii
                    save_ascii = self.getProperty("Save Ascii").value
                    if save_ascii is True:
                        file_prefix = self.getProperty("Outputfile Prefix").value
                        file_extension = self.getProperty("Outputfile Extension").value
                        option_overwrite = self.getProperty("Overwrite existing ASCII output files").value
                        api.TOFTOFSaveAscii(InputWorkspace=group_sofqw, OutputFilename=file_prefix,
                                            Extension=file_extension, OverwriteExistingFiles=option_overwrite)

        print 'list of unchanged workspaces', list_unchanged_ws

    # To do : delete intermediate cloned workspace
        # Tof2dE
        #if self.getProperty("Convert tof to DeltaE").value is True:
            # DetectorEfficiencyCorUser
        #    if self.getProperty("Correct Sample data for detector efficiency").value is not True:
        #        api.DeleteWorkspace(group_deteff)
            # CorrectKiKf
        #    if self.getProperty("Apply Ki/Kf correction").value is not True:
        #        api.DeleteWorkspace(group_kikf)

        #if self.getProperty("Normalize to Monitor counts").value is not True or nb_vana_sets==0:
        #    api.DeleteWorkspace(group_mon_eff)

        #if nb_vana_sets == 0:
        #    api.DeleteWorkspace(group_detsens)
        #else:
        #    if self.getProperty("Normalize to Vanadium").value is not True:
        #        api.DeleteWorkspace(group_detsens)
        #    else:
        #        api.DeleteWorkspace(group_sample_vana)

        #if norm_to_ec is not True:
        #    api.DeleteWorkspace(group_sample_minus_ec)
    # ----------------------------------------------------------------------------------------
    def _get_Sample_Runs(self, rlist):
        """
        returns the runs as a list of strings
        used only for sample data
        """
        rlvals = rlist.split(';')
        run_list = []
        for rlval in rlvals:
            # name not already stored
            if not rlval in run_list:
                print rlval, run_list
                run_list.append(rlval)
        return run_list

    def _find_or_load(self, rlist):
        """
        test if all entries have to be loaded or are workspaces
        True: must load data
        False: find already existing workspaces
        """
        return all(not AnalysisDataService.doesExist(single_entry) for single_entry in rlist.split(','))

    def _load_data(self, data, output_name_gp, output_name_clean_log):
        if self._find_or_load(data):
            api.Load(Filename=data, OutputWorkspace=output_name_gp)
        else:
            to_group_names = list()
            for single_entry in data.split(','):
                ws = AnalysisDataService.retrieve(single_entry)
                to_group_names.append(ws)
            api.GroupWorkspaces(InputWorkspaces=to_group_names, OutputWorkspace=output_name_gp)
        api.TOFTOFCleanSampleLogs(InputWorkspaces=mtd[output_name_gp], OutputWorkspace=output_name_clean_log)
        if len(data.split(',')) > 1:
            api.DeleteWorkspace(mtd[output_name_gp])
        return mtd[output_name_clean_log]

    # ----------------------------------------------------------------------------------------
    # Mask detectors
    def _remove_empty_detectors(self, group):
        """
        mask detectors with no counts
        """
        (wsOut, NumberOfFailures) = api.FindDetectorsOutsideLimits(group)
        print 'Number of detectors with no count', NumberOfFailures
        api.MaskDetectors(group, MaskedWorkspace=wsOut)
        api.DeleteWorkspace(wsOut)

    def _mask_detectors_by_id(self, ws, range_ids):
        """
        mask detectors according to their ids
        """
        list_iddetectors = []
        print 'range_ids', range_ids
        for item in range_ids.split(','):
            print 'item in list of ids', item
            if '-' not in item:
                list_iddetectors.append(int(item))
            else:
                rangeid = [int(item.split('-')[0]), int(item.split('-')[1])]
                list_iddetectors.extend(range(min(rangeid), max(rangeid) + 1))
        api.MaskDetectors(ws, DetectorList=list_iddetectors)

    def _mask_detectors_by_angle(self, ws, range_angles):
        """
        mask detectors according to their angles
        """
        summed_blocks = range_angles.split(";")
        for block in summed_blocks:
            element = block.split(',')
            if element[0] >= element[1]:
                raise ValueError('Wrong values for angles in mask')
            min_angle_to_mask = float(element[0])
            max_angle_to_mask = float(element[1])
            detectors_to_mask = []
            if isinstance(ws, WorkspaceGroup):
                for i in range(ws.getItem(0).getNumberHistograms()):
                    det = ws.getItem(0).getInstrument().getDetector(i)
                    if min_angle_to_mask <= det.getNumberParameter("TwoTheta")[0] <= max_angle_to_mask:
                        detectors_to_mask.append(det.getID())
                for i in range(ws.getNumberOfEntries()):
                    api.MaskDetectors(ws.getItem(i), DetectorList=detectors_to_mask)
            else:
                for i in range(ws.getNumberHistograms()):
                    det = ws.getInstrument().getDetector(i)
                    if min_angle_to_mask <= det.getNumberParameter("TwoTheta")[0] <= max_angle_to_mask:
                        detectors_to_mask.append(det.getID())
                api.MaskDetectors(ws, DetectorList=detectors_to_mask)

    # ----------------------------------------------------------------------------------------
    def _treat_empty_cans(self, groupMonEff, nb_datasets, nb_vanasets, nb_ecsets):
        """
        Treatment of Empty cans if defined
        To do: add EC for Vanadium
        """
        group_sample = api.GroupWorkspaces([groupMonEff.getItem(i).getName() for i in range(nb_datasets)])
        if nb_ecsets == 1:
            ec_ws = groupMonEff.getItem(nb_datasets+nb_vanasets)
            api.Scale(InputWorkspace=ec_ws, OutputWorkspace='EC_trans',
                      Factor=self.getProperty("Scale factor to Empty cans data").value)
        elif nb_ecsets == 2:
            multipl_factor = self.getProperty("Scale factor to Empty cans data").value
            ec_ws = groupMonEff.getItem(nb_datasets+nb_vanasets)
            api.Scale(InputWorkspace=ec_ws, OutputWorkspace='EC_trans', Factor=multipl_factor)

        api.Minus(LHSWorkspace=group_sample, RHSWorkspace='EC_trans', OutputWorkspace='group_sample_minus')

        return AnalysisDataService.retrieve('group_sample_minus')

    #---------------------------------------------------------------------------------------
    def _rebin_group(self, group_ws):
        """
        Apply Rebin algorithm to group of workspaces
        """
        rebiningInEnergy = self.getProperty("EnergyBins").value
        nb_ws = group_ws.getNumberOfEntries()
        for i in range(nb_ws):
            group_ws.getItem(i).setDistribution(True)
        api.Rebin(InputWorkspace=group_ws, OutputWorkSpace='group_rebin', Params=rebiningInEnergy)
        for i in range(nb_ws):
            group_ws.getItem(i).setDistribution(False)
        return mtd['group_rebin']

    #---------------------------------------------------------------------------------------
    def _sofqw_group(self, group_ws):
        """
        Apply SofQW to a group of workspaces
        """
        rebining_in_q = self.getProperty("MomentumTransferBins").value
        # Calculate energy for all sample data
        # nb_ws = groupws.getNumberOfEntries()
        ws = group_ws.getItem(0)
        nrj = ws.getRun().getLogData('Ei').value
        # output_ws = list()
        # for i in range(nb_ws):
        #    ws = groupws.getItem(i)
        #    nrj = ws.getRun().getLogData('Ei').value
        group_sofqw = api.SofQW(InputWorkspace=group_ws, QAxisBinning=rebining_in_q, EMode='Direct', EFixed=nrj,
                                 Method='NormalisedPolygon')
        #    output_ws.append(ws_sofqw)
        # group_sofqw = api.GroupWorkspaces(output_ws)
        api.DeleteWorkspace(ws)
        return group_sofqw

# ----------------------------------------------------------------------------------------
# Register algorithm with Mantid.
AlgorithmFactory.subscribe(TOFTOFReduction)
