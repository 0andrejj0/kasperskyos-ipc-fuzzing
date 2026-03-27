project(coverage_collector LANGUAGES CXX)

add_library(coverage_collector coverage_collector.cpp)

include (platform/install)

export_targets(
    TARGETS
        coverage_collector
    GENERATE_CONFIG_IN)