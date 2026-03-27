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

target_link_libraries(Fuzzer
    PRIVATE
        fuzztest::fuzztest_gtest_main
        vfs::client
        kosipc::kosipc
        $<LINK_LIBRARY:WHOLE_ARCHIVE,coverage_mapper::reciever>)
set_target_properties (Fuzzer PROPERTIES vfs::entity_REPLACEMENT "")

target_compile_options(Fuzzer PRIVATE
    -g
    -DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION
    -UNDEBUG
    -fsanitize-coverage=inline-8bit-counters # TODO investigate why fail with trace-pc-guard
    -fsanitize-coverage=trace-cmp
    -fprofile-instr-generate
    -fcoverage-mapping
)

target_link_options(Fuzzer PRIVATE
    "LINKER:--allow-shlib-undefined"
    "LINKER:--unresolved-symbols=ignore-all"
)
