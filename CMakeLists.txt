cmake_minimum_required(VERSION 3.15)
project(dv-transaction-trace VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set output directories
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Packages directory - can be overridden via -DPACKAGES_DIR=...
if(NOT DEFINED PACKAGES_DIR)
    set(PACKAGES_DIR "${CMAKE_SOURCE_DIR}/packages")
endif()

message(STATUS "Using PACKAGES_DIR: ${PACKAGES_DIR}")

# Paths
set(PROTOC_EXECUTABLE "${PACKAGES_DIR}/protobuf/bin/protoc")
set(PROTOBUF_INCLUDE_DIR "${PACKAGES_DIR}/protobuf/include")
set(PERFETTO_ROOT_DIR "${PACKAGES_DIR}/perfetto-src")
set(PERFETTO_PROTO_DIR "${PERFETTO_ROOT_DIR}/protos")

# Generated output directories (in build directory)
set(GENERATED_CPP_DIR "${CMAKE_BINARY_DIR}/generated/cpp")
set(GENERATED_PYTHON_DIR "${CMAKE_BINARY_DIR}/generated/python")

# Create output directories
file(MAKE_DIRECTORY ${GENERATED_CPP_DIR})
file(MAKE_DIRECTORY ${GENERATED_PYTHON_DIR})

# Ensure protoc is executable
if(EXISTS ${PROTOC_EXECUTABLE})
    file(CHMOD ${PROTOC_EXECUTABLE}
         PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE
                     GROUP_READ GROUP_EXECUTE
                     WORLD_READ WORLD_EXECUTE)
    message(STATUS "Found protoc: ${PROTOC_EXECUTABLE}")
else()
    message(FATAL_ERROR "protoc not found at ${PROTOC_EXECUTABLE}")
endif()

# Verify protoc works
execute_process(
    COMMAND ${PROTOC_EXECUTABLE} --version
    OUTPUT_VARIABLE PROTOC_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE PROTOC_RESULT
)

if(NOT PROTOC_RESULT EQUAL 0)
    message(FATAL_ERROR "protoc executable is not working properly")
endif()

message(STATUS "Using protoc version: ${PROTOC_VERSION}")

# Find essential proto files for trace/track_event
# Core trace files
file(GLOB TRACE_CORE_PROTOS
    "${PERFETTO_PROTO_DIR}/perfetto/trace/trace.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/trace_packet.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/trace_packet_defaults.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/clock_snapshot.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/trace_uuid.proto"
)

# Track event protos (non-chrome specific)
file(GLOB TRACK_EVENT_PROTOS
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/track_event.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/track_descriptor.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/thread_descriptor.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/process_descriptor.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/counter_descriptor.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/debug_annotation.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/log_message.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/source_location.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/trace/track_event/task_execution.proto"
)

# Interned data (required by track_event)
file(GLOB INTERNED_DATA_PROTOS
    "${PERFETTO_PROTO_DIR}/perfetto/trace/interned_data/interned_data.proto"
)

# Common protos (required by core trace)
file(GLOB COMMON_PROTOS
    "${PERFETTO_PROTO_DIR}/perfetto/common/builtin_clock.proto"
    "${PERFETTO_PROTO_DIR}/perfetto/common/descriptor.proto"
)

# Combine all required protos
set(PERFETTO_PROTO_FILES
    ${TRACE_CORE_PROTOS}
    ${TRACK_EVENT_PROTOS}
    ${INTERNED_DATA_PROTOS}
    ${COMMON_PROTOS}
)

list(LENGTH PERFETTO_PROTO_FILES PROTO_COUNT)
message(STATUS "Total proto files to generate: ${PROTO_COUNT}")

# Generate C++ sources from proto files
set(GENERATED_CPP_SOURCES)
set(GENERATED_CPP_HEADERS)

foreach(PROTO_FILE ${PERFETTO_PROTO_FILES})
    # Get relative path from proto directory's parent (perfetto root)
    file(RELATIVE_PATH PROTO_REL_PATH ${PERFETTO_ROOT_DIR} ${PROTO_FILE})
    
    # Compute output paths
    string(REGEX REPLACE "\\.proto$" ".pb.cc" CPP_SOURCE ${PROTO_REL_PATH})
    string(REGEX REPLACE "\\.proto$" ".pb.h" CPP_HEADER ${PROTO_REL_PATH})
    
    set(CPP_SOURCE_FULL "${GENERATED_CPP_DIR}/${CPP_SOURCE}")
    set(CPP_HEADER_FULL "${GENERATED_CPP_DIR}/${CPP_HEADER}")
    
    list(APPEND GENERATED_CPP_SOURCES ${CPP_SOURCE_FULL})
    list(APPEND GENERATED_CPP_HEADERS ${CPP_HEADER_FULL})
    
    # Create directory for output file
    get_filename_component(CPP_OUTPUT_DIR ${CPP_SOURCE_FULL} DIRECTORY)
    file(MAKE_DIRECTORY ${CPP_OUTPUT_DIR})
    
    # Add custom command to generate C++ files
    add_custom_command(
        OUTPUT ${CPP_SOURCE_FULL} ${CPP_HEADER_FULL}
        COMMAND ${PROTOC_EXECUTABLE}
            --proto_path=${PERFETTO_ROOT_DIR}
            --cpp_out=${GENERATED_CPP_DIR}
            ${PROTO_FILE}
        DEPENDS ${PROTO_FILE}
        COMMENT "Generating C++ code from ${PROTO_REL_PATH}"
        VERBATIM
    )
endforeach()

# Generate Python sources from proto files
set(GENERATED_PYTHON_SOURCES)

foreach(PROTO_FILE ${PERFETTO_PROTO_FILES})
    # Get relative path from proto directory's parent (perfetto root)
    file(RELATIVE_PATH PROTO_REL_PATH ${PERFETTO_ROOT_DIR} ${PROTO_FILE})
    
    # Compute output paths
    string(REGEX REPLACE "\\.proto$" "_pb2.py" PYTHON_SOURCE ${PROTO_REL_PATH})
    
    set(PYTHON_SOURCE_FULL "${GENERATED_PYTHON_DIR}/${PYTHON_SOURCE}")
    
    list(APPEND GENERATED_PYTHON_SOURCES ${PYTHON_SOURCE_FULL})
    
    # Create directory for output file
    get_filename_component(PYTHON_OUTPUT_DIR ${PYTHON_SOURCE_FULL} DIRECTORY)
    file(MAKE_DIRECTORY ${PYTHON_OUTPUT_DIR})
    
    # Add custom command to generate Python files
    add_custom_command(
        OUTPUT ${PYTHON_SOURCE_FULL}
        COMMAND ${PROTOC_EXECUTABLE}
            --proto_path=${PERFETTO_ROOT_DIR}
            --python_out=${GENERATED_PYTHON_DIR}
            ${PROTO_FILE}
        DEPENDS ${PROTO_FILE}
        COMMENT "Generating Python code from ${PROTO_REL_PATH}"
        VERBATIM
    )
endforeach()

# Create custom targets for generated code
add_custom_target(generate_cpp_protos ALL
    DEPENDS ${GENERATED_CPP_SOURCES} ${GENERATED_CPP_HEADERS}
    COMMENT "Generating all C++ protobuf sources"
)

add_custom_target(generate_python_protos ALL
    DEPENDS ${GENERATED_PYTHON_SOURCES}
    COMMENT "Generating all Python protobuf sources"
)

# Export compile commands for IDEs
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Print summary
message(STATUS "========================================")
message(STATUS "Configuration Summary:")
message(STATUS "  Source directory: ${CMAKE_SOURCE_DIR}")
message(STATUS "  Build directory: ${CMAKE_BINARY_DIR}")
message(STATUS "  Protoc: ${PROTOC_EXECUTABLE}")
message(STATUS "  Proto files: ${PROTO_COUNT}")
message(STATUS "  C++ output: ${GENERATED_CPP_DIR}")
message(STATUS "  Python output: ${GENERATED_PYTHON_DIR}")
message(STATUS "")
message(STATUS "Generated files will be placed in:")
message(STATUS "  ${GENERATED_CPP_DIR}/protos/")
message(STATUS "  ${GENERATED_PYTHON_DIR}/protos/")
message(STATUS "")
message(STATUS "Note: To build a C++ library, install libprotobuf-dev")
message(STATUS "      and link against the generated .pb.cc files")
message(STATUS "========================================")

# Build C++ library
option(BUILD_CPP_LIBRARY "Build C++ implementation library" ON)

if(BUILD_CPP_LIBRARY)
    message(STATUS "Building C++ shared library (standalone, no protobuf dependencies)")
    
    # Add C++ library - shared library by default
    add_library(dvtt SHARED
        src/dvtt.cpp
    )
    
    target_include_directories(dvtt PUBLIC
        ${CMAKE_SOURCE_DIR}/src
        ${GENERATED_CPP_DIR}
    )
    
    set_target_properties(dvtt PROPERTIES
        CXX_STANDARD 17
        CXX_STANDARD_REQUIRED ON
        POSITION_INDEPENDENT_CODE ON
        VERSION 1.0.0
        SOVERSION 1
    )
    
    # Install rules
    install(TARGETS dvtt
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
        RUNTIME DESTINATION bin
    )
    
    install(FILES src/include/dvtt.h
        DESTINATION include
    )
    
    message(STATUS "C++ shared library target 'dvtt' configured (standalone mode)")
    message(STATUS "Note: Library uses built-in protobuf writer, no external dependencies")
endif()

# Testing
option(BUILD_TESTS "Build unit tests" ON)

if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()