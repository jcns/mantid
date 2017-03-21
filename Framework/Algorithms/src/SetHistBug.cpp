#include "MantidAlgorithms/SetHistBug.h"
#include "MantidAPI/WorkspaceFactory.h"
#include "MantidAPI/MatrixWorkspace.h"
#include "MantidDataObjects/EventWorkspace.h"


namespace Mantid {
namespace Algorithms {

using Mantid::Kernel::Direction;
using Mantid::API::WorkspaceProperty;

// Register the algorithm into the AlgorithmFactory
DECLARE_ALGORITHM(SetHistBug)

//----------------------------------------------------------------------------------------------

/// Algorithms name for identification. @see Algorithm::name
const std::string SetHistBug::name() const { return "SetHistBug"; }

/// Algorithm's version for identification. @see Algorithm::version
int SetHistBug::version() const { return 1; }

/// Algorithm's category for identification. @see Algorithm::category
const std::string SetHistBug::category() const {
  return "TODO: FILL IN A CATEGORY";
}

/// Algorithm's summary for use in the GUI and help. @see Algorithm::summary
const std::string SetHistBug::summary() const {
  return "TODO: FILL IN A SUMMARY";
}

//----------------------------------------------------------------------------------------------
/** Initialize the algorithm's properties.
 */
void SetHistBug::init() {
  declareProperty(
      Kernel::make_unique<WorkspaceProperty<DataObjects::EventWorkspace>>("InputWorkspace", "",
                                                             Direction::Input),
      "An input workspace.");
  declareProperty(
      Kernel::make_unique<WorkspaceProperty<API::Workspace>>("OutputWorkspace", "",
                                                             Direction::Output),
      "An output workspace.");
}

//----------------------------------------------------------------------------------------------
/** Execute the algorithm.
 */
void SetHistBug::exec() {
    const DataObjects::EventWorkspace_sptr inputWS = getProperty("InputWorkspace");
    HistogramData::BinEdges dummy{0.0, 1.0};
    Mantid::API::MatrixWorkspace_sptr outputWS =  Mantid::API::WorkspaceFactory::Instance().create(inputWS);
    outputWS->setHistogram(0, dummy);

    setProperty("OutputWorkspace", outputWS);
}

} // namespace Algorithms
} // namespace Mantid
