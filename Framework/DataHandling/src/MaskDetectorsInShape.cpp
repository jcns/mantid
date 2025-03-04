// Mantid Repository : https://github.com/mantidproject/mantid
//
// Copyright &copy; 2018 ISIS Rutherford Appleton Laboratory UKRI,
//     NScD Oak Ridge National Laboratory, European Spallation Source
//     & Institut Laue - Langevin
// SPDX - License - Identifier: GPL - 3.0 +
#include "MantidDataHandling/MaskDetectorsInShape.h"

#include "MantidAPI/MatrixWorkspace.h"
#include "MantidAPI/SpectrumInfo.h"
#include "MantidGeometry/Instrument/DetectorInfo.h"
#include "MantidKernel/ArrayProperty.h"
#include "MantidKernel/MandatoryValidator.h"

namespace Mantid {
namespace DataHandling {
// Register the algorithm into the algorithm factory
DECLARE_ALGORITHM(MaskDetectorsInShape)

using namespace Kernel;
using namespace API;

void MaskDetectorsInShape::init() {
  declareProperty(
      make_unique<WorkspaceProperty<>>("Workspace", "", Direction::InOut),
      "The input workspace");
  declareProperty("ShapeXML", "",
                  boost::make_shared<MandatoryValidator<std::string>>(),
                  "The XML definition of the user defined shape.");
  declareProperty("IncludeMonitors", false,
                  "Whether to include monitors if "
                  "they are contained in the shape "
                  "(default false)");
}

void MaskDetectorsInShape::exec() {
  // Get the input workspace
  MatrixWorkspace_sptr WS = getProperty("Workspace");

  const bool includeMonitors = getProperty("IncludeMonitors");
  const std::string shapeXML = getProperty("ShapeXML");

  std::vector<int> foundDets =
      runFindDetectorsInShape(WS, shapeXML, includeMonitors);
  if (foundDets.empty()) {
    g_log.information(
        "No detectors were found in the shape, nothing was masked");
    return;
  }
  runMaskDetectors(WS, foundDets);
  setProperty("Workspace", WS);
}

/// Run the FindDetectorsInShape Child Algorithm
std::vector<int> MaskDetectorsInShape::runFindDetectorsInShape(
    API::MatrixWorkspace_sptr workspace, const std::string shapeXML,
    const bool includeMonitors) {
  IAlgorithm_sptr alg = createChildAlgorithm("FindDetectorsInShape");
  alg->setPropertyValue("IncludeMonitors", includeMonitors ? "1" : "0");
  alg->setPropertyValue("ShapeXML", shapeXML);
  alg->setProperty<MatrixWorkspace_sptr>("Workspace", workspace);
  try {
    if (!alg->execute()) {
      throw std::runtime_error("FindDetectorsInShape Child Algorithm has not "
                               "executed successfully\n");
    }
  } catch (std::runtime_error &) {
    g_log.error(
        "Unable to successfully execute FindDetectorsInShape Child Algorithm");
    throw;
  }
  progress(0.5);

  // extract the results
  return alg->getProperty("DetectorList");
}

void MaskDetectorsInShape::runMaskDetectors(
    API::MatrixWorkspace_sptr workspace, const std::vector<int> &detectorIds) {
  auto &detectorInfo = workspace->mutableDetectorInfo();
  for (const auto &id : detectorIds)
    detectorInfo.setMasked(detectorInfo.indexOf(id), true);
  const auto &spectrumInfo = workspace->spectrumInfo();
  for (size_t i = 0; i < spectrumInfo.size(); ++i)
    if (spectrumInfo.hasDetectors(i) && spectrumInfo.isMasked(i))
      workspace->getSpectrum(i).clearData();
  progress(1);
}

} // namespace DataHandling
} // namespace Mantid
