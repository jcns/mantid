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
#include "MantidTestHelpers/FakeObjects.h"
#include "MantidKernel/IValidator.h"
#include <vector>
#include <gmock/gmock.h>

using namespace Mantid::API;
using namespace Mantid::Kernel;

class WorkspaceListPropertyTest : public CxxTest::TestSuite
{
private:

  class MockValidator : public Mantid::Kernel::IValidator
  {
  public:
    MockValidator(){}
    virtual ~MockValidator(){}
    MOCK_CONST_METHOD0(clone, IValidator_sptr());
    MOCK_CONST_METHOD1(check, std::string(const boost::any&));
  };

  class MyAlgorithm: public Mantid::API::Algorithm
  {
  public:
    MyAlgorithm()
    {
      this->setRethrows(true);
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
          new WorkspaceListProperty<Workspace>("MyProperty", std::vector<Workspace_sptr>(0)));
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


  //------------------------------------------------------------------------------
  // Functional Testing
  //------------------------------------------------------------------------------

  void test_construction_minimalistic()
  {
    AnalysisDataServiceImpl& ads = AnalysisDataService::Instance();
    ads.add("MyWorkspace", boost::make_shared<WorkspaceTester>());

    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<Workspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<MatrixWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<IMDHistoWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<IMDEventWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<ITableWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));
    TS_ASSERT_THROWS_NOTHING(WorkspaceListProperty<ISplittersWorkspace>("MyWorkspaceProperty", "MyWorkspace", Direction::Input));

    ads.remove("MyWorkspace");
  }

  void test_construction()
  {
    WorkspaceListProperty<Workspace> workspaceListProperty("MyWorkspaceProperty", "MyWorkspace1, MyWorkspace2", Direction::Input, PropertyMode::Optional);
    auto workspaceNames = workspaceListProperty.getWorkspaceNames();
    TS_ASSERT_EQUALS(2, workspaceNames.size());
    TS_ASSERT_EQUALS(workspaceNames.front(), "MyWorkspace1");
    TS_ASSERT_EQUALS(workspaceNames.back(), "MyWorkspace2");
    TS_ASSERT_EQUALS(workspaceListProperty.isOptional(), true)
  }

  void test_construct_throws_with_ws_outside_ads()
  {
    auto ws = boost::make_shared<WorkspaceTester>(); // Not in ADS
    WorkspaceListProperty<Workspace>::WorkspacePropertyListType vec;
    vec.push_back(ws);

    TS_ASSERT_THROWS( WorkspaceListProperty<Workspace>("MyWorkspaceProperty", vec), std::invalid_argument&);
  }

  void test_construct_from_workspaces()
  {
    auto a = boost::make_shared<WorkspaceTester>();
    auto b = boost::make_shared<WorkspaceTester>();
    AnalysisDataService::Instance().add("a", a);
    AnalysisDataService::Instance().add("b", b);

    WorkspaceListProperty<Workspace>::WorkspacePropertyListType vec;
    vec.push_back(a);
    vec.push_back(b);

    WorkspaceListProperty<Workspace>* property;
    TS_ASSERT_THROWS_NOTHING(property = new WorkspaceListProperty<Workspace>("MyWorkspaceProperty", vec, Direction::Input,  PropertyMode::Mandatory));

    TS_ASSERT_EQUALS(2, property->getWorkspaceNames().size());

    delete property;
    AnalysisDataService::Instance().remove("a");
    AnalysisDataService::Instance().remove("b");
  }

  void test_contruct_as_optional()
  {
    const std::string defaultArg  = "";
    TS_ASSERT_THROWS( WorkspaceListProperty<Workspace>("MyProperty", defaultArg, Direction::Input, PropertyMode::Mandatory), std::invalid_argument);
    TS_ASSERT_THROWS_NOTHING( WorkspaceListProperty<Workspace>("MyProperty", defaultArg, Direction::Input, PropertyMode::Optional))
  }

  void test_copy_construction()
  {
    WorkspaceListProperty<Workspace> a("PropA", "a1, a2", Direction::Input, PropertyMode::Optional);
    WorkspaceListProperty<Workspace> b(a);
    TS_ASSERT_EQUALS(a.getWorkspaceNames(), b.getWorkspaceNames());
    TS_ASSERT_EQUALS(a.isOptional(), b.isOptional());
  }

  void test_assignment()
  {
    auto a = boost::make_shared<WorkspaceTester>();
    AnalysisDataService::Instance().add("a", a);
    WorkspaceListProperty<Workspace> propA("PropA", "a", Direction::Input, PropertyMode::Mandatory);
    WorkspaceListProperty<Workspace> propB("PropB", "", Direction::Input, PropertyMode::Optional);
    propB = propA;
    TS_ASSERT_EQUALS(propA.getWorkspaceNames(), propB.getWorkspaceNames());
    TS_ASSERT_EQUALS(propA.isOptional(), propB.isOptional());
    AnalysisDataService::Instance().remove("a");
  }

  void test_validator_usage()
  {
    using namespace testing;
    std::string okString = "";

    boost::shared_ptr<MockValidator> validator = boost::make_shared<MockValidator>();
    EXPECT_CALL(*validator.get(), check(_)).Times(3).WillRepeatedly(Return(okString));


    auto ws = boost::make_shared<WorkspaceTester>();
    AnalysisDataService::Instance().add("ws", ws);
    WorkspaceListProperty<Workspace> prop("Prop", "ws, ws, ws", Direction::Input, PropertyMode::Mandatory, validator);

    TSM_ASSERT("Should repeatedly call the validator", Mock::VerifyAndClearExpectations(validator.get()));
    AnalysisDataService::Instance().remove(ws->name());
  }

  //------------------------------------------------------------------------------
  // Integration type testing. Test that the Property works nicely via the PropertyManager interfaces (such as Algorithm).
  //------------------------------------------------------------------------------
  void test_setPropertyValue_throws_with_workspace_not_in_ADS()
  {
    MyAlgorithm alg;
    alg.initialize();
    TSM_ASSERT_THROWS("Workspaces are not in the ADS, so should throw", alg.setPropertyValue("MyProperty", "a"), std::invalid_argument&);
  }

  void test_setPropertyValue_with_single_workspace()
  {
    AnalysisDataServiceImpl& ads = AnalysisDataService::Instance();
    ads.add("a", boost::make_shared<WorkspaceTester>());

    MyAlgorithm alg;
    alg.initialize();
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("MyProperty", "a"));

    ads.remove("a");
  }

  void test_septPropertyValue_with_multiple_workspaces()
  {
    AnalysisDataServiceImpl& ads = AnalysisDataService::Instance();
    ads.add("a", boost::make_shared<WorkspaceTester>());
    ads.add("b", boost::make_shared<WorkspaceTester>());

    MyAlgorithm alg;
    alg.initialize();
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("MyProperty", "a, b"));

    ads.remove("a");
    ads.remove("b");
  }

  void test_septPropertyValue_with_multiple_workspaces_last_doesnt_exist()
  {
    AnalysisDataServiceImpl& ads = AnalysisDataService::Instance();
    ads.add("a", boost::make_shared<WorkspaceTester>());

    MyAlgorithm alg;
    alg.initialize();
    TSM_ASSERT_THROWS("Not ALL Workspaces are in the ADS, so should throw", alg.setPropertyValue("MyProperty", "a, b"), std::invalid_argument&);

    ads.remove("a");
  }

  void test_set_and_get_Property_as_vector()
  {
    AnalysisDataServiceImpl& ads = AnalysisDataService::Instance();
    auto a = boost::make_shared<WorkspaceTester>();
    auto b = boost::make_shared<WorkspaceTester>();
    ads.add("a", a);
    ads.add("b", b);

    MyAlgorithm alg;
    alg.initialize();

    auto vecIn = std::vector<Workspace_sptr>();
    vecIn.push_back(a);
    vecIn.push_back(b);

    alg.setProperty("MyProperty", vecIn);
    // Now fetch the property.
    std::vector<Workspace_sptr> vecOut = alg.getProperty("MyProperty");

    TS_ASSERT_EQUALS(vecIn.size(), vecOut.size());
    TS_ASSERT_EQUALS(vecIn, vecOut);

    ads.remove("a");
    ads.remove("b");
  }

  void test_getPropertyValue()
  {
    AnalysisDataServiceImpl& ads = AnalysisDataService::Instance();
    auto a = boost::make_shared<WorkspaceTester>();
    auto b = boost::make_shared<WorkspaceTester>();
    ads.add("a", a);
    ads.add("b", b);

    MyAlgorithm alg;
    alg.initialize();

    auto vecIn = std::vector<Workspace_sptr>();
    vecIn.push_back(a);
    vecIn.push_back(b);

    alg.setProperty("MyProperty", vecIn);
    // Now fetch the property.
    std::string outStr = alg.getPropertyValue("MyProperty");

    TS_ASSERT_EQUALS("a,b", outStr);

    ads.remove("a");
    ads.remove("b");
  }

};


#endif /* MANTID_API_WORKSPACELISTPROPERTYTEST_H_ */
