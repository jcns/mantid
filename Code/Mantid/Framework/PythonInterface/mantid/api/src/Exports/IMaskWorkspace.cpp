#include "MantidAPI/IMaskWorkspace.h"
#include "MantidAPI/MatrixWorkspace.h"
#include "MantidPythonInterface/kernel/Registry/DataItemInterface.h"
#include <boost/python/class.hpp>

using Mantid::API::IMaskWorkspace;
using Mantid::API::IMaskWorkspace_sptr;
using Mantid::API::MatrixWorkspace;
using namespace boost::python;
namespace Registry = Mantid::PythonInterface::Registry;

/** Python exports of the Mantid::API::IMaskWorkspace class. */
void export_IMaskWorkspace()
{
  class_<IMaskWorkspace, bases<MatrixWorkspace>, boost::noncopyable>("IMaskWorkspace", no_init)
      .def("getNumberMasked", &IMaskWorkspace::getNumberMasked, args("self"),
           "Total number of masked pixels")
      ;

  Registry::DataItemInterface<IMaskWorkspace> entry;
  entry.castFromID("MaskWorkspace");
}
