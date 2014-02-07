#include "MantidAPI/IMaskWorkspace.h"
#include "MantidPythonInterface/kernel/SharedPtrToPythonMacro.h"
#include "MantidPythonInterface/kernel/Registry/RegisterSingleValueHandler.h"

#include <boost/python/class.hpp>

using Mantid::API::IMaskWorkspace;
using Mantid::API::IMaskWorkspace_sptr;
using namespace boost::python;

/** Python exports of the Mantid::API::IMaskWorkspace class. */
void export_IMaskWorkspace()
{
  REGISTER_SHARED_PTR_TO_PYTHON(IMaskWorkspace);

  class_<IMaskWorkspace, boost::noncopyable>("IMaskWorkspace", no_init)
      .def("getNumberMasked", &IMaskWorkspace::getNumberMasked, args("self"),
           "Total number of masked pixels")
      ;

  REGISTER_SINGLEVALUE_HANDLER(IMaskWorkspace_sptr);
}
