#ifndef MANTID_API_WORKSPACELISTPROPERTYTEST_H_
#define MANTID_API_WORKSPACELISTPROPERTYTEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidAPI/WorkspaceListProperty.h"
#include "MantidAPI/Workspace.h"
#include "MantidAPI/MatrixWorkspace.h"
#include "MantidAPI/IMDHistoWorkspace.h"
#include "MantidAPI/IMDEventWorkspace.h"
#include "MantidAPI/ITableWorkspace.h"
#include "MantidAPI/IEventWorkspace.h"
#include "MantidAPI/ISplittersWorkspace.h"
#include "MantidAPI/Algorithm.h"
#include <vector>

using namespace Mantid::API;
using namespace Mantid::Kernel;

class WorkspaceListPropertyTest : public CxxTest::TestSuite
{
private:

  class MyAlgorithm: public Mantid::API::Algorithm
  {
  public:
    MyAlgorithm()
    {
    }

    virtual int version() const
    {
      return 1;
    }

    virtual const std::string name() const
    {
      return "MyAlgorithm";
    }

    virtual void init()
    {
      declareProperty(
          new PropertyWithValue<std::vector<Workspace_sptr> >("MyProperty", std::vector<Workspace_sptr>(0)));
    }

    virtual void exec()
    {
      std::vector<Workspace_sptr> val = getProperty("MyProperty");
    }

    virtual ~MyAlgorithm()
    {

    }
  };

public:
  // This pair of boilerplate methods prevent the suite being created statically
  // This means the constructor isn't called when running other tests
  static WorkspaceListPropertyTest *createSuite() { return new WorkspaceListPropertyTest(); }
  static void destroySuite( WorkspaceListPropertyTest *suite ) { delete suite; }


  void testConstructionMinimalistic()
  {
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<Workspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<MatrixWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<IMDHistoWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<IMDEventWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<ITableWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<ISplittersWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
  }

  void testConstruction()
  {
    WorkspaceListProperty<Workspace> workspaceListProperty("MyWorkspaceProperty", "MyWorkspace1, MyWorkspace2", Direction::Input, PropertyMode::Mandatory);
    auto workspaceNames = workspaceListProperty.getWorkspaceNames();
    TS_ASSERT_EQUALS(2, workspaceNames.size());
    TS_ASSERT_EQUALS(workspaceNames.front(), "MyWorkspace1");
    TS_ASSERT_EQUALS(workspaceNames.back(), "MyWorkspace2");
    TS_ASSERT_EQUALS(workspaceListProperty.isOptional(), false)
  }

  void testCopyConstruction()
  {
    WorkspaceListProperty<Workspace> a("PropA", "a1, a2", Direction::Input, PropertyMode::Mandatory);
    WorkspaceListProperty<Workspace> b(a);
    TS_ASSERT_EQUALS(a.getWorkspaceNames(), b.getWorkspaceNames());
    TS_ASSERT_EQUALS(a.isOptional(), b.isOptional());
  }

  void testGetPropertyValue()
  {
    MyAlgorithm alg;
    alg.initialize();
    alg.setPropertyValue("MyProperty", "a, b, c");
    //alg.execute();
  }



/*
  void xtestGetPropertyValue()
  {
    MyAlgorithm alg;
    alg.initialize();
    alg.setProperty("MyProperty", std::vector<Workspace_sptr>("MyProperty", "MyWorkspace1, MyWorkspace2"));
  }
*/


};


#endif /* MANTID_API_WORKSPACELISTPROPERTYTEST_H_ */
