cmake_minimum_required(VERSION 3.15)

# Try to find Google Test
find_package(GTest)

if(GTest_FOUND)
    message(STATUS "Found Google Test - building C++ unit tests")
    
    # Add test executables
    add_executable(test_dvtt_basic
        test_basic.cpp
    )
    
    target_link_libraries(test_dvtt_basic
        dvtt
        GTest::GTest
        GTest::Main
    )
    
    target_include_directories(test_dvtt_basic PRIVATE
        ${CMAKE_SOURCE_DIR}/src
    )
    
    # Register tests with CTest
    add_test(NAME test_dvtt_basic COMMAND test_dvtt_basic)
    
    message(STATUS "C++ unit tests configured")
else()
    message(WARNING "Google Test not found - C++ unit tests will not be built")
    message(WARNING "Install libgtest-dev or set GTest_DIR")
endif()
