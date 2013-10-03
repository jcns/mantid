#ifndef MANTID_API_WORKSPACELISTPROPERTY_H_
#define MANTID_API_WORKSPACELISTPROPERTY_H_

#include <vector>
#include <algorithm>
#include <boost/algorithm/string.hpp>
#include "MantidKernel/System.h"
#include "MantidAPI/WorkspaceProperty.h"

namespace Mantid
{
  namespace API
  {

    /** WorkspaceListProperty : Property with value that constrains the contents to be a list of workspaces of a single type.

     Copyright &copy; 2013 ISIS Rutherford Appleton Laboratory & NScD Oak Ridge National Laboratory

     This file is part of Mantid.

     Mantid is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 3 of the License, or
     (at your option) any later version.

     Mantid is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

     File change history is stored at: <https://github.com/mantidproject/mantid>
     Code Documentation is available at: <http://doxygen.mantidproject.org>
     */
    template<typename TYPE = MatrixWorkspace>
    class DLLExport WorkspaceListProperty: public Mantid::Kernel::PropertyWithValue<
        std::vector<boost::shared_ptr<TYPE> > >
    {
    public:

      /// Typedef the value type of this property with value.
      typedef std::vector<boost::shared_ptr<TYPE> > WorkspacePropertyListType;
      typedef Kernel::PropertyWithValue<WorkspacePropertyListType> SuperClass;

      /**
       * Helper method to split a comma separated string into a vector of strings.
       */
      std::vector<std::string> namesToVector(std::string names)
      {
        names.erase(std::remove_if(names.begin(), names.end(), (int (*)(int))std::isspace), names.end());
        std::vector<std::string> splitNames;
        boost::split(splitNames, names, boost::is_any_of(","));
        return splitNames;
      }

      /** Constructor.
       *  Sets the property and workspace names but initialises the workspace pointers to null.
       *  @param name :: The name to assign to the property
       *  @param wsNames :: The names of the workspaces
       *  @param direction :: Whether this is a Direction::Input, Direction::Output or Direction::InOut (Input & Output) workspace
       *  @param validator :: The (optional) validator to use for this property
       *  @throw std::out_of_range if the direction argument is not a member of the Direction enum (i.e. 0-2)
       */
      explicit WorkspaceListProperty( const std::string &name, const std::string &wsNames, const unsigned int direction=Mantid::Kernel::Direction::Input,
                                Mantid::Kernel::IValidator_sptr validator = Mantid::Kernel::IValidator_sptr(new Kernel::NullValidator)) :
      Mantid::Kernel::PropertyWithValue<WorkspacePropertyListType>( name, WorkspacePropertyListType(0), validator, direction ),
      m_optional(PropertyMode::Mandatory), m_workspaceNames(0)
     // ,m_workspaceName( wsName ), m_initialWSName( wsName ), m_optional(PropertyMode::Mandatory), m_locking(LockMode::Lock)
    {
      m_workspaceNames = namesToVector(wsNames);
      const std::string errorMsg = syncWorkspaces();
      if(!errorMsg.empty() && !this->isOptional())
      {
        throw std::invalid_argument(errorMsg);
      }
    }
    
    /** Constructor.
    *  Sets the property and workspace names but initialises the workspace pointers to null.
    *  @param name :: The name to assign to the property
    *  @param wsNames :: The name of the workspace
    *  @param direction :: Whether this is a Direction::Input, Direction::Output or Direction::InOut (Input & Output) workspace
    *  @param optional :: Flag to determine whether this property is optional or not.
    *  @param validator :: The (optional) validator to use for this property
    *  @throw std::out_of_range if the direction argument is not a member of the Direction enum (i.e. 0-2)
    */
    explicit WorkspaceListProperty( const std::string &name, const std::string &wsNames, const unsigned int direction, const PropertyMode::Type optional,
                                Mantid::Kernel::IValidator_sptr validator = Mantid::Kernel::IValidator_sptr(new Kernel::NullValidator)) :
      Mantid::Kernel::PropertyWithValue<WorkspacePropertyListType>( name, WorkspacePropertyListType(0), validator, direction ),
      m_optional(optional), m_workspaceNames(0)
    {
      m_workspaceNames = namesToVector(wsNames);
      const std::string errorMsg = syncWorkspaces();
      if(!errorMsg.empty() && !this->isOptional())
      {
        throw std::invalid_argument(errorMsg);
      }
    }


    explicit WorkspaceListProperty( const std::string &name, const WorkspacePropertyListType workspaces, const unsigned int direction=Mantid::Kernel::Direction::Input, const PropertyMode::Type optional = PropertyMode::Mandatory,
                                Mantid::Kernel::IValidator_sptr validator = Mantid::Kernel::IValidator_sptr(new Kernel::NullValidator)) :
      Mantid::Kernel::PropertyWithValue<WorkspacePropertyListType>( name, WorkspacePropertyListType(0), validator, direction ),
      m_optional(optional), m_workspaceNames(0)
    {
      Kernel::PropertyWithValue< WorkspacePropertyListType>::m_value = workspaces;
      syncNames();
    }


    /// Copy constructor, the default name stored in the new object is the same as the default name from the original object
    WorkspaceListProperty( const WorkspaceListProperty& right ) :
    SuperClass( right ),
    m_optional(right.m_optional), m_workspaceNames(right.m_workspaceNames)
    {
    }

    /** Set the name of the workspace.
    *  Also tries to retrieve it from the AnalysisDataService.
    *  @param value :: The new name for the workspace
    *  @return
    */
    virtual std::string setValue( const std::string& value )
    {
      m_workspaceNames = namesToVector(value);
      return syncWorkspaces();
    }

    std::string syncWorkspaces()
    {
      // Try and get the workspace from the ADS, but don't worry if we can't
      WorkspacePropertyListType temp;
      for( auto it = m_workspaceNames.begin(); it != m_workspaceNames.end(); ++it)
      {
        try
        {
          auto name = *it;
          auto ws = AnalysisDataService::Instance().retrieve(*it);
          temp.push_back(AnalysisDataService::Instance().retrieveWS<TYPE>(*it));
        }
        catch (Kernel::Exception::NotFoundError &)
        {
          // Set to null property if not found
          this->clear();
          //the workspace name is not reset here, however.
        }
      }
      SuperClass::m_value = temp;
      return isValid();
    }

    std::string missingWorkspaceErrorMessage(const std::string& wsName) const
    {
      std::stringstream stream;
      stream << "Workspace called '" << wsName << "' is not in the Workspace List and is unknown to Mantid";
      return stream.str();
    }

    void syncNames() const
    {
      std::vector<std::string> temp;
      for(auto it = SuperClass::m_value.begin(); it != SuperClass::m_value.end(); ++it)
      {
        const std::string wsName = (*it)->name();
        if(!AnalysisDataService::Instance().doesExist(wsName))
        {
          throw std::invalid_argument(missingWorkspaceErrorMessage(wsName));
        }
        temp.push_back( (*it)->name() );
      }
      m_workspaceNames = temp;
    }

    /** Checks whether the entered workspaces are valid.
    *  To be valid, in addition to satisfying the conditions of any validators. Input ones must point to
    *  workspaces of the correct type.
    *  @returns A user level description of the problem or "" if it is valid.
    */
    std::string isValid() const
    {
      //start with the no error condition
      std::string error = "";
      // If an input (or inout) workspace, must point to something, although it doesn't have to have a name
      // unless it's optional
      if ( this->direction() == Kernel::Direction::Input || this->direction() == Kernel::Direction::InOut )
      {
        for(auto it = m_workspaceNames.begin(); it != m_workspaceNames.end(); ++it)
        {
          try
          {
            auto wksp = AnalysisDataService::Instance().retrieve(*it);
          }
          catch( Kernel::Exception::NotFoundError &)
          {
            return missingWorkspaceErrorMessage(*it);
          }
        }
      }
      // Call superclass method to access any attached validators (which do their own logging)
      return Kernel::PropertyWithValue<WorkspacePropertyListType >::isValid();
    }

    void clear()
    {
      SuperClass::m_value = WorkspacePropertyListType(0);
    }

    virtual std::string value() const
    {
      this->syncNames();
      std::stringstream result;
      std::size_t vsize = m_workspaceNames.size();
      for (std::size_t i = 0; i < vsize; ++i)
      {
        result << m_workspaceNames[i];
        if (i + 1 != vsize)
        result << ",";
      }
      return result.str();
    }

    /// Is the input workspace property optional?
    virtual bool isOptional() const
    {
      return m_optional == PropertyMode::Optional;
    }

    /**
     * Getter for the workspace names.
     */
    std::vector<std::string> getWorkspaceNames() const
    {
      return m_workspaceNames;
    }

    virtual ~WorkspaceListProperty()
    {
    }

  private:
    /// Flag indicating whether the type is optional or not.
    PropertyMode::Type m_optional;
    /// Keys to the workspaces in the ADS
    mutable std::vector<std::string> m_workspaceNames;

  }
      ;

    } // namespace API
  } // namespace Mantid

#endif  /* MANTID_API_WORKSPACELISTPROPERTY_H_ */
