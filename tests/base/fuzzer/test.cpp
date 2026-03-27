#include "test/Fuzzer.edl.cpp.h"
#include "test/IEcho.idl.cpp.h"

#include <kl/CoverageMapper.cdl.cpp.h>
#include <component/coverage_mapper/coverage_mapper_reciever.h>

#include <kosipc/application.h>
#include <kosipc/connect_dcm_publication.h>
#include <kosipc/api.h>

#include <kos/trace.h>

#include <fuzztest/fuzztest.h>
#include <fuzztest/googletest_adaptor.h>
#include <fuzztest/googletest_fixture_adapter.h>
#include <gtest/gtest.h>

#include <cstdio>
#include <iostream>
#include <optional>
#include <chrono>
#include <thread>
#include <unistd.h>

#include <fcntl.h>
#include <sys/mman.h>

using namespace std::chrono_literals;

__attribute__((constructor))
void mapCoverage()
{
}

// class EchoIpcFixture
// {
// public:
//     EchoIpcFixture()
//         : m_app(kosipc::MakeApplicationPureClient())
//         , m_proxy(m_app.MakeProxy<kosipc::stdcpp::test::IEcho>(kosipc::ConnectDcmPublication()))
//     {
//     }

//     void Echo(int i)
//     {
//         uint32_t res{0};
//         m_proxy->Echo(i, res);
//         EXPECT_EQ(i, res);
//     }

//     kosipc::Application m_app;
//     kosipc::unique_ptr<kosipc::stdcpp::test::IEcho> m_proxy;
// };
// FUZZ_TEST_F(EchoIpcFixture, Echo)
//     .WithDomains(fuzztest::Positive<uint32_t>());

void TestEchoIpc(uint32_t i)
{
    kosipc::Application app = kosipc::MakeApplicationPureClient();

    auto proxy = app.MakeProxy<kosipc::stdcpp::test::IEcho>(kosipc::ConnectDcmPublication());
    uint32_t res;
    proxy->Echo(i, res);

    EXPECT_EQ(i, res);
}
FUZZ_TEST(IPC, TestEchoIpc)
    .WithDomains(fuzztest::Positive<uint32_t>());


void TestEchoLocal(uint32_t i)
{
    // std::cerr << "LOCAL RUN " << i << '\n';
    // EXPECT_NE(i, 123);
}
FUZZ_TEST(LOCAL, TestEchoLocal)
    .WithDomains(fuzztest::Positive<uint32_t>());


int main(int argc, char** argv) {

    // if (dup2(STDOUT_FILENO, STDERR_FILENO) != 0) {
    //     std::cerr << "Failed to redirect stdout to stderr" << std::endl;
    // }

    // std::cerr << "START\n";

    kosipc::Application app = kosipc::MakeApplicationAutodetect();
    kosipc::components::Root root;
    coverage_mapper::RunCoverageMapperReciever(root.mapper, app);

    char* custom_argv[] = {
        "my_fuzzer",
        "--fork=false",
        "--timeout=1",
        "--runs=10",
        nullptr
    };

    std::cerr << "KEK 1\n";

    int custom_argc = sizeof(custom_argv)/sizeof(custom_argv[0]) - 1;

    std::cerr << "KEK 2\n";

    testing::InitGoogleTest(&custom_argc, const_cast<char**>(custom_argv));
    std::cerr << "KEK 3\n";

    char** argvv = custom_argv;
    GOOGLEFUZZTEST_REGISTER_FOR_GOOGLETEST(fuzztest::RunMode::kUnitTest, &custom_argc, &argvv);

    std::cerr << "KEK 4\n";

    return RUN_ALL_TESTS();
}
