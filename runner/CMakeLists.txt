cmake_minimum_required(VERSION 3.21)

project(fuzztest_runner LANGUAGES CXX)

include(platform)
initialize_platform()

include(platform/install)
include(platform/nk)

find_package(coverage_mapper REQUIRED)
find_package(GTest REQUIRED)
find_package(absl REQUIRED)
find_package(re2 REQUIRED)
find_package(fuzztest REQUIRED)
find_package(kosipc REQUIRED)

add_library(fuzztest_runner_main
    STATIC
        src/main.cpp)

target_link_libraries(fuzztest_runner_main
    PUBLIC
        fuzztest::fuzztest_gtest_main
        kosipc::kosipc
        $<LINK_LIBRARY:WHOLE_ARCHIVE,coverage_mapper::reciever>)

add_nk_edl (FUZZER_EDL "xdl/FuzztestRunner.edl"
            NK_MODULE  "kl"
            LANG       "CXX")

add_dependencies (fuzztest_runner_main FUZZER_EDL)
bind_nk_targets (fuzztest_runner_main FUZZER_EDL)

export_targets(
    TARGETS
        fuzztest_runner_main
        FUZZER_EDL
    GENERATE_CONFIG_IN)
