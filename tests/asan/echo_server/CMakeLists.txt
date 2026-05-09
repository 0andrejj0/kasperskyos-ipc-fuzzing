find_package(vfs REQUIRED)
find_package(logrr_cpp REQUIRED)
find_package(kosipc REQUIRED)

add_executable(EchoServer main.cpp)
target_link_libraries(EchoServer
    PRIVATE
    vfs::client
    kosipc::kosipc
    $<LINK_LIBRARY:WHOLE_ARCHIVE,coverage_mapper::provider>)
set_target_properties (EchoServer PROPERTIES vfs::entity_REPLACEMENT "")

target_compile_options(EchoServer PRIVATE
    -g
    -UNDEBUG
    -fsanitize=undefined,address
    -fsanitize-coverage=trace-pc-guard
    -fprofile-instr-generate
    -fcoverage-mapping
    -O1
)

target_link_options(EchoServer PRIVATE
    -fsanitize=undefined,address
    -fsanitize-coverage=trace-pc-guard
    -fprofile-instr-generate
    -fcoverage-mapping
)

add_nk_idl(SERVER_IDL "IEcho.idl"
            NK_MODULE  "test"
            LANG       "CXX")

add_nk_edl (SERVER_EDL "Echo.edl"
            NK_MODULE  "test"
            LANG       "CXX")

bind_nk_targets (SERVER_EDL SERVER_IDL)
bind_nk_targets (EchoServer SERVER_EDL)
