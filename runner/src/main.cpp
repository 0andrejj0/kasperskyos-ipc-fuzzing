#include<kl/FuzztestRunner.edl.cpp.h>

#include<kl/CoverageMapper.cdl.cpp.h>
#include<component/coverage_mapper/coverage_mapper_reciever.h>

#include<fuzztest/fuzztest.h>
#include<fuzztest/googletest_adaptor.h>
#include<fuzztest/googletest_fixture_adapter.h>
#include<gtest/gtest.h>

#include <kosipc/api.h>
#include <kos/trace.h>

#include <thread>
#include <chrono>

using namespace std::chrono_literals;

int main(int argc, char** argv) {

    INFO(FUZZTEST_RUNNER, "Starting fuzzing");

    kosipc::Application app = kosipc::MakeApplicationAutodetect();
    kosipc::components::Root root;

    coverage_mapper::RunCoverageMapperReciever(root.mapper, app);
    coverage_mapper::WaitCoverageReady();

    char* custom_argv[] = {
        "kos_ipc_fuzzer",
        "--fork=false",
        "--timeout=10",
        "--runs=1",
        "--verbose=1",
        nullptr
    };

    int custom_argc = sizeof(custom_argv)/sizeof(custom_argv[0]) - 1;

    testing::InitGoogleTest(&custom_argc, const_cast<char**>(custom_argv));

    char** argvv = custom_argv;
    GOOGLEFUZZTEST_REGISTER_FOR_GOOGLETEST(fuzztest::RunMode::kFuzz, &custom_argc, &argvv);

    auto rc = RUN_ALL_TESTS();

    std::this_thread::sleep_for(1s);

    coverage_mapper::Print();

    coverage_mapper::Stop();

    return rc;
}
