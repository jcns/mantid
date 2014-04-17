#ifndef MANTID_DATAHANDLING_LOADMLZTEST_H_
#define MANTID_DATAHANDLING_LOADMLZTEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidDataHandling/LoadMLZ.h"

#include "MantidAPI/AnalysisDataService.h"

using Mantid::DataHandling::LoadMLZ;

class LoadMLZTest : public CxxTest::TestSuite
{
public:
  // This pair of boilerplate methods prevent the suite being created statically
  // This means the constructor isn't called when running other tests
  static LoadMLZTest *createSuite() { return new LoadMLZTest(); }
  static void destroySuite( LoadMLZTest *suite ) { delete suite; }


  void test_Init()
  {
    LoadMLZ loader;
    TS_ASSERT_EQUALS( loader.version(), 1 )
  }
  
//  LoadMLZTest() :
//          m_dataFile("toftofdata.nxs") {
//  }

  void testName() {
      LoadMLZ loader;
      TS_ASSERT_EQUALS( loader.name(), "LoadMLZ");
  }
//  void test_exec()
//  {
//    // Name of the output workspace.
//    std::string outWSName("LoadMLZTest_OutputWS");
  
//    LoadMLZ alg;
//    TS_ASSERT_THROWS_NOTHING( alg.initialize() )
//    TS_ASSERT( alg.isInitialized() )
//    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("REPLACE_PROPERTY_NAME_HERE!!!!", "value") );
//    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("OutputWorkspace", outWSName) );
//    TS_ASSERT_THROWS_NOTHING( alg.execute(); );
//    TS_ASSERT( alg.isExecuted() );
    
//    // Retrieve the workspace from data service. TODO: Change to your desired type
//    Workspace_sptr ws;
//    TS_ASSERT_THROWS_NOTHING( ws = AnalysisDataService::Instance().retrieveWS<Workspace>(outWSName) );
//    TS_ASSERT(ws);
//    if (!ws) return;
    
//    // TODO: Check the results
    
//    // Remove workspace from the data service.
//    AnalysisDataService::Instance().remove(outWSName);
//  }
  
//  void test_Something()
//  {
//    TSM_ASSERT( "You forgot to write a test!", 0);
//  }


};


#endif /* MANTID_DATAHANDLING_LOADMLZTEST_H_ */
