cmake_minimum_required(VERSION 3.12)
project(zrc_wrapper)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find Python
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Find or fetch pybind11
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    message(STATUS "pybind11 not found, fetching from GitHub...")
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG v2.11.1
    )
    FetchContent_MakeAvailable(pybind11)
endif()

# SDK paths
set(SDK_ROOT ${PROJECT_SOURCE_DIR}/..)
set(SDK_INCLUDE ${SDK_ROOT}/include)
set(SDK_LIBS ${SDK_ROOT}/libs)
set(DEMO_LIBS ${SDK_ROOT}/Demo/libs)

# Create Python module from generated bindings
pybind11_add_module(zrc_sdk bindings/zrc_bindings.cpp)

# Include directories
target_include_directories(zrc_sdk PRIVATE
    ${SDK_INCLUDE}
    ${SDK_INCLUDE}/include
    ${SDK_INCLUDE}/include/ServiceComponents
    ${SDK_ROOT}/Demo/include/libuv/include
)

# Link directories
target_link_directories(zrc_sdk PRIVATE
    ${SDK_LIBS}
    ${DEMO_LIBS}
)

# Link libraries
if(UNIX AND NOT APPLE)
    target_link_libraries(zrc_sdk PRIVATE
        ZRCSdk
        atomic
        pthread
        dl
    )
    # Set RPATH for runtime linking
    set_target_properties(zrc_sdk PROPERTIES
        INSTALL_RPATH "${SDK_LIBS}"
        BUILD_WITH_INSTALL_RPATH TRUE
    )
elseif(UNIX AND APPLE)
    target_link_libraries(zrc_sdk PRIVATE
        "-framework ZRCSdk"
    )
elseif(WIN32)
    target_link_libraries(zrc_sdk PRIVATE
        ZRCSdk.lib
    )
endif()

# Install target
install(TARGETS zrc_sdk DESTINATION ${PROJECT_SOURCE_DIR}/service)
