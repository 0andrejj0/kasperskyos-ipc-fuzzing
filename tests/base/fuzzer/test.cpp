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


///// GENERATED CODE
#include <fuzztest/fuzztest.h>
#include <fuzztest/domain.h>

#include <cstdint>
#include <string>
#include <vector>

template <typename T>
auto GetDefaultMutator();

template<>
auto GetDefaultMutator<kosipc::stdcpp::test::TestStructure>() {
    return fuzztest::StructOf<kosipc::stdcpp::test::TestStructure>(
        fuzztest::Arbitrary<uint64_t>(), // param1
        fuzztest::Arbitrary<uint32_t>() // param2
    );
}

// Mutator for struct TestStructureBig using StructOf
template<>
auto GetDefaultMutator<kosipc::stdcpp::test::TestStructureBig>() {
    return fuzztest::StructOf<kosipc::stdcpp::test::TestStructureBig>(
        GetDefaultMutator<kosipc::stdcpp::test::TestStructure>(), // param1
        fuzztest::Arbitrary<uint32_t>() // param2
    );
}

/////

using namespace std::chrono_literals;

__attribute__((constructor))
void mapCoverage()
{
}

class EchoIpcFixture
{
public:
    EchoIpcFixture()
        : m_app(kosipc::MakeApplicationPureClient())
        , m_proxy(m_app.MakeProxy<kosipc::stdcpp::test::IEcho>(kosipc::ConnectDcmPublication()))
    {
    }

    void Echo(kosipc::stdcpp::test::TestStructureBig input)
    {
        kosipc::stdcpp::test::TestStructureBig result = input;
        m_proxy->Echo(input, result);
        EXPECT_EQ(input.param1.param1, result.param1.param1);
        EXPECT_EQ(input.param1.param2, result.param1.param2);
        EXPECT_EQ(input.param2, result.param2);
    }

    kosipc::Application m_app;
    kosipc::unique_ptr<kosipc::stdcpp::test::IEcho> m_proxy;
};
FUZZ_TEST_F(EchoIpcFixture, Echo)
    .WithDomains(GetDefaultMutator<kosipc::stdcpp::test::TestStructureBig>());

void TestEchoIpc(kosipc::stdcpp::test::TestStructureBig input)
{
    kosipc::Application app = kosipc::MakeApplicationPureClient();

    auto proxy = app.MakeProxy<kosipc::stdcpp::test::IEcho>(kosipc::ConnectDcmPublication());
    kosipc::stdcpp::test::TestStructureBig result = input;
    proxy->Echo(input, result);

    EXPECT_EQ(input.param1.param1, result.param1.param1);
    EXPECT_EQ(input.param1.param2, result.param1.param2);
    EXPECT_EQ(input.param2, result.param2);
}
FUZZ_TEST(IPC, TestEchoIpc)
    .WithDomains(GetDefaultMutator<kosipc::stdcpp::test::TestStructureBig>());


// void TestEchoLocal(uint32_t i)
// {
//     // std::cerr << "LOCAL RUN " << i << '\n';
//     EXPECT_NE(i, 123);
// }
// FUZZ_TEST(LOCAL, TestEchoLocal)
//     .WithDomains(fuzztest::Positive<uint32_t>());


int main(int argc, char** argv) {

    if (dup2(STDOUT_FILENO, STDERR_FILENO) != 0) {
        std::cerr << "Failed to redirect stdout to stderr" << std::endl;
    }

    std::cerr << "START\n";

    kosipc::Application app = kosipc::MakeApplicationAutodetect();
    kosipc::components::Root root;

    char* custom_argv[] = {
        "my_fuzzer",
        "--fork=false",
        "--timeout=1",
        "--runs=10",
        "--verbose=1",
        nullptr
    };

    int custom_argc = sizeof(custom_argv)/sizeof(custom_argv[0]) - 1;

    testing::InitGoogleTest(&custom_argc, const_cast<char**>(custom_argv));

    char** argvv = custom_argv;
    GOOGLEFUZZTEST_REGISTER_FOR_GOOGLETEST(fuzztest::RunMode::kUnitTest, &custom_argc, &argvv);

    coverage_mapper::RunCoverageMapperReciever(root.mapper, app);

    coverage_mapper::WaitCoverageReady();

    auto rc = RUN_ALL_TESTS();
    coverage_mapper::Stop();
    return rc;
}
