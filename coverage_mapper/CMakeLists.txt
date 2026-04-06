cmake_minimum_required(VERSION 3.21)

project(coverage_mapper LANGUAGES CXX)

include(platform)
initialize_platform()

include(platform/install)
include(platform/nk)

add_nk_idl(SERVER_IDL "${CMAKE_CURRENT_SOURCE_DIR}/xdl/ICoverageMapper.idl"
            NK_MODULE  "kl"
            LANG       "CXX")

add_nk_cdl(SERVER_CDL "${CMAKE_CURRENT_SOURCE_DIR}/xdl/CoverageMapper.cdl"
            NK_MODULE  "kl"
            LANG       "CXX")

bind_nk_targets(SERVER_IDL SERVER_CDL)

include_directories(include)

add_library(provider
    STATIC
        src/provider.cpp
        src/shared_memory_buffer.cpp)
add_library(reciever
    STATIC
        src/reciever.cpp
        src/shared_memory_buffer.cpp)
set_target_properties(provider PROPERTIES OUTPUT_NAME "${PROJECT_NAME}_provider")
set_target_properties(reciever PROPERTIES OUTPUT_NAME "${PROJECT_NAME}_reciever")

bind_nk_targets (reciever SERVER_IDL SERVER_CDL)
bind_nk_targets (provider SERVER_IDL)

export_targets(
    TARGETS
        SERVER_IDL
        SERVER_CDL
        provider
        reciever
    GENERATE_CONFIG_IN)

install(DIRECTORY
    ${CMAKE_CURRENT_BINARY_DIR}/_headers_/kl/
    DESTINATION include/kl)

install(FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/include/coverage_mapper_reciever.h
    DESTINATION include/component/coverage_mapper)
