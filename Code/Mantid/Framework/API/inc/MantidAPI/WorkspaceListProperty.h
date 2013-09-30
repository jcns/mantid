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
  template <typename TYPE = MatrixWorkspace>
  class DLLExport WorkspaceListProperty : public  Mantid::Kernel::PropertyWithValue<std::vector<boost::shared_ptr<TYPE> > >
  {
  public:

    /// Typedef the value type of this property with value.
    typedef std::vector<boost::shared_ptr<TYPE> > WorkspacePropertyListType;

    /**
     * Helper method to split a comma separated string into a vector of strings.
     */
    std::vector<std::string> namesToVector(std::string names)
    {
      names.erase(std::remove_if(names.begin(), names.end(), (int(*)(int))std::isspace), names.end());
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
    explicit WorkspaceListProperty( const std::string &name, const std::string &wsNames, const unsigned int direction,
                                Mantid::Kernel::IValidator_sptr validator = Mantid::Kernel::IValidator_sptr(new Kernel::NullValidator)) :
      Mantid::Kernel::PropertyWithValue<WorkspacePropertyListType>( name, WorkspacePropertyListType(0), validator, direction ),
      m_optional(PropertyMode::Mandatory), m_workspaceNames(0)
     // ,m_workspaceName( wsName ), m_initialWSName( wsName ), m_optional(PropertyMode::Mandatory), m_locking(LockMode::Lock)
    {
      m_workspaceNames = namesToVector(wsNames);
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
    }


    /// Copy constructor, the default name stored in the new object is the same as the default name from the original object
    WorkspaceListProperty( const WorkspaceListProperty& right ) :
    Kernel::PropertyWithValue< WorkspacePropertyListType >( right ),
    m_optional(right.m_optional)
    {
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
    std::vector<std::string> m_workspaceNames;

  };


} // namespace API
} // namespace Mantid

#endif  /* MANTID_API_WORKSPACELISTPROPERTY_H_ */
