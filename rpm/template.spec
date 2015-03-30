Name:           ros-indigo-object-recognition-tod
Version:        0.5.2
Release:        0%{?dist}
Summary:        ROS object_recognition_tod package

Group:          Development/Libraries
License:        BSD
URL:            http://wg-perception.github.io/tod/
Source0:        %{name}-%{version}.tar.gz

Requires:       ros-indigo-ecto
Requires:       ros-indigo-ecto-opencv
Requires:       ros-indigo-ecto-openni
Requires:       ros-indigo-object-recognition-core
Requires:       ros-indigo-opencv-candidate
BuildRequires:  eigen3-devel
BuildRequires:  ros-indigo-catkin
BuildRequires:  ros-indigo-cmake-modules
BuildRequires:  ros-indigo-ecto
BuildRequires:  ros-indigo-object-recognition-core
BuildRequires:  ros-indigo-opencv-candidate

%description
Textured Object Recognition a standard bag of features approach

%prep
%setup -q

%build
# In case we're installing to a non-standard location, look for a setup.sh
# in the install tree that was dropped by catkin, and source it.  It will
# set things like CMAKE_PREFIX_PATH, PKG_CONFIG_PATH, and PYTHONPATH.
if [ -f "/opt/ros/indigo/setup.sh" ]; then . "/opt/ros/indigo/setup.sh"; fi
mkdir -p obj-%{_target_platform} && cd obj-%{_target_platform}
%cmake .. \
        -UINCLUDE_INSTALL_DIR \
        -ULIB_INSTALL_DIR \
        -USYSCONF_INSTALL_DIR \
        -USHARE_INSTALL_PREFIX \
        -ULIB_SUFFIX \
        -DCMAKE_INSTALL_PREFIX="/opt/ros/indigo" \
        -DCMAKE_PREFIX_PATH="/opt/ros/indigo" \
        -DSETUPTOOLS_DEB_LAYOUT=OFF \
        -DCATKIN_BUILD_BINARY_PACKAGE="1" \

make %{?_smp_mflags}

%install
# In case we're installing to a non-standard location, look for a setup.sh
# in the install tree that was dropped by catkin, and source it.  It will
# set things like CMAKE_PREFIX_PATH, PKG_CONFIG_PATH, and PYTHONPATH.
if [ -f "/opt/ros/indigo/setup.sh" ]; then . "/opt/ros/indigo/setup.sh"; fi
cd obj-%{_target_platform}
make %{?_smp_mflags} install DESTDIR=%{buildroot}

%files
/opt/ros/indigo

%changelog
* Mon Mar 30 2015 Vincent Rabaud <vincent.rabaud@gmail.com> - 0.5.2-0
- Autogenerated by Bloom

