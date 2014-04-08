//------------------------------------------------------------------------------
// This is a global 'include' file for the GSoap DOI generated files that
// disables warnings in automatically generated code, which we do not want to touch.
//------------------------------------------------------------------------------

#if defined(__GNUC__) && !(defined(__INTEL_COMPILER))
  #pragma GCC diagnostic ignored "-Wunused-parameter"
#elif defined(_WIN32)
  #pragma warning( disable: 4100 )
#endif

#include "GSoapGenerated/ICatDOIC.cpp"
#include "GSoapGenerated/ICatDOIDOIPortBindingProxy.cpp"
