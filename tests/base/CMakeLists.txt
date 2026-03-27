project (base_test)

include(platform)
initialize_platform(FORCE_STATIC)

include (platform/nk)
include (platform/image)

find_package (coverage_mapper REQUIRED)

add_subdirectory(echo_server)
add_subdirectory(fuzzer)
add_subdirectory(einit)
