cmake_minimum_required (VERSION 3.25)

project(fuzztest LANGUAGES CXX)

include(platform)
initialize_platform()

set(CMAKE_CXX_STANDART 17)

set(ABSL_ENABLE_INSTALL ON)
set(ABSL_BUILD_TESTING OFF)
add_subdirectory(abseil-cpp)

#set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D__linux__=1")
set(FUZZTEST_TESTING OFF)
add_subdirectory(fuzztest)

##### install fuzztest
install(DIRECTORY fuzztest/fuzztest
    DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)

include (platform/install)
export_targets(
    TARGETS
        fuzztest_gtest_main
        fuzztest_serialization
        fuzztest_io
        fuzztest_coverage
        fuzztest_logging
        fuzztest_fixture_driver
        fuzztest_type_support
        fuzztest_seed_seq
        fuzztest_fuzztest
        fuzztest_registry
        fuzztest_googletest_adaptor
        fuzztest_regexp_dfa
        fuzztest_runtime
        fuzztest_table_of_recent_compares
        fuzztest_compatibility_mode
        fuzztest_meta
        fuzztest_any
        fuzztest_registration
        fuzztest_domain
    GENERATE_CONFIG_IN
    CONFIG_IN_ADDON "find_dependency(GTest)\n")

#####
