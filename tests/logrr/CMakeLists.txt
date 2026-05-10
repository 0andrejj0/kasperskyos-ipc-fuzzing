cmake_minimum_required(VERSION 3.19)

project (base_test)

include(platform)
initialize_platform(FORCE_STATIC)

include (platform/nk)
include (platform/image)

find_package (coverage_mapper REQUIRED)

add_subdirectory(logrr_server)
add_subdirectory(fuzzer)
add_subdirectory(einit)
