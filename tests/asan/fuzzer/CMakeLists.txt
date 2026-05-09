add_executable(Fuzzer test.cpp)

add_nk_edl (FUZZER_EDL "Fuzzer.edl"
            NK_MODULE  "test"
            LANG       "CXX")

add_dependencies (Fuzzer FUZZER_EDL)
bind_nk_targets (Fuzzer FUZZER_EDL)

find_package(vfs REQUIRED)

find_package(GTest REQUIRED)
find_package(absl REQUIRED)
find_package(re2 REQUIRED)
find_package(fuzztest REQUIRED)
find_package(kosipc REQUIRED)

find_package(fuzztest_runner REQUIRED)

set(GENERATED_HEADER_DIR ${CMAKE_CURRENT_BINARY_DIR}/generated)
set(GENERATED_HEADER_PATH ${GENERATED_HEADER_DIR}/generated_fuzztest.h)
set(IDL_FILE "${CMAKE_CURRENT_SOURCE_DIR}/../echo_server/IEcho.idl")

add_custom_target(GenerateFuzzTestHeader
    COMMAND ${CMAKE_COMMAND} -E make_directory ${GENERATED_HEADER_DIR}
    COMMAND idl_to_fuzztest
        -I ${SYSROOT}/include
        --nk-driver ${SDK_PREFIX}/toolchain/bin/nk-driver
        -o ${GENERATED_HEADER_PATH}
        ${IDL_FILE}
    BYPRODUCTS ${GENERATED_HEADER_PATH}
    COMMENT "Generating fuzztest header from Echo.idl"
    VERBATIM
)

add_dependencies(Fuzzer GenerateFuzzTestHeader)
target_include_directories(Fuzzer PRIVATE ${GENERATED_HEADER_DIR})

target_link_libraries(Fuzzer
    PRIVATE
        fuzztest_runner::fuzztest_runner_main
        vfs::client)
set_target_properties (Fuzzer PROPERTIES vfs::entity_REPLACEMENT "")

target_compile_options(Fuzzer PRIVATE
    -g
    -UNDEBUG
)

target_link_options(Fuzzer PRIVATE
    "LINKER:--allow-shlib-undefined"
    "LINKER:--unresolved-symbols=ignore-all"
)
