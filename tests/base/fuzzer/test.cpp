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
// Auto-generated mutators for IDL interfaces
// Generated from multiple IDL files

// Forward declaration of GetDefaultMutator
template<typename T>
auto GetDefaultMutator();

// Packages: kl.core.Types, test.IEcho

// Type definitions resolution:
// Char -> UInt8
// Boolean -> UInt8
// SizeT -> UInt64
// TrRetcode -> SInt32
// UCoreString -> string<1023>
// ExecutableBuildId -> sequence
// TimeUnit -> UInt64
// Uuid -> array
// TestString -> string<5120>
// TestBytes -> bytes<277>

// Mutator for struct TrNoneParam
template<>
auto GetDefaultMutator<kosipc::stdcpp::kl::core::TrNoneParam>() {
    return fuzztest::StructOf<kosipc::stdcpp::kl::core::TrNoneParam>(
        fuzztest::Arbitrary<uint32_t>() /* empty */
    );
}
// Mutator for struct TrRoundRobinParam
template<>
auto GetDefaultMutator<kosipc::stdcpp::kl::core::TrRoundRobinParam>() {
    return fuzztest::StructOf<kosipc::stdcpp::kl::core::TrRoundRobinParam>(
        fuzztest::Arbitrary<uint64_t>() /* sec */,
        fuzztest::Arbitrary<uint32_t>() /* nsec */
    );
}
// Mutator for struct TimeSpec
template<>
auto GetDefaultMutator<kosipc::stdcpp::kl::core::TimeSpec>() {
    return fuzztest::StructOf<kosipc::stdcpp::kl::core::TimeSpec>(
        fuzztest::Arbitrary<int64_t>() /* sec */,
        fuzztest::Arbitrary<uint32_t>() /* nsec */
    );
}
// Mutator for struct TestStructure
template<>
auto GetDefaultMutator<kosipc::stdcpp::test::TestStructure>() {
    return fuzztest::StructOf<kosipc::stdcpp::test::TestStructure>(
        fuzztest::Arbitrary<uint64_t>() /* param1 */,
        fuzztest::Arbitrary<uint32_t>() /* param2 */
    );
}
// Mutator for struct TestStructureBig
template<>
auto GetDefaultMutator<kosipc::stdcpp::test::TestStructureBig>() {
    return fuzztest::StructOf<kosipc::stdcpp::test::TestStructureBig>(
        GetDefaultMutator<kosipc::stdcpp::test::TestStructure>() /* param1 */,
        fuzztest::Arbitrary<uint32_t>() /* param2 */
    );
}
// Mutator for struct TestStructureStr
template<>
auto GetDefaultMutator<kosipc::stdcpp::test::TestStructureStr>() {
    return fuzztest::StructOf<kosipc::stdcpp::test::TestStructureStr>(
        fuzztest::Arbitrary<std::vector<std::byte>>().WithMaxSize(277) /* param1 */,
        fuzztest::Arbitrary<std::string>().WithMaxSize(5120) /* param2 */,
        fuzztest::VectorOf(GetDefaultMutator<kosipc::stdcpp::test::TestStructure>()).WithMaxSize(3) /* param3 */
    );
}

// Input parameter structures for interface methods
// Input parameters structure for IEcho::Echo
struct IEcho_Echo_InputParams {
    kosipc::stdcpp::test::TestStructureBig input;
};
// Mutator for input params of IEcho::Echo
template<>
auto GetDefaultMutator<IEcho_Echo_InputParams>() {
    return fuzztest::StructOf<IEcho_Echo_InputParams>(
        GetDefaultMutator<kosipc::stdcpp::test::TestStructureBig>() /* input */
    );
}

// Output parameter structures for interface methods
// Output parameters structure for IEcho::Echo
struct IEcho_Echo_OutputParams {
    kosipc::stdcpp::test::TestStructureBig output;
};
// Mutator for output params of IEcho::Echo
template<>
auto GetDefaultMutator<IEcho_Echo_OutputParams>() {
    return fuzztest::StructOf<IEcho_Echo_OutputParams>(
        GetDefaultMutator<kosipc::stdcpp::test::TestStructureBig>() /* output */
    );
}

// Input variants (all possible input parameter combinations)
// Variant containing all possible input parameter combinations for interface IEcho
    using IEcho_AllInputParams = std::variant<IEcho_Echo_InputParams>;

    // Mutator for the variant
    template<>
    auto GetDefaultMutator<IEcho_AllInputParams>() {
        return fuzztest::VariantOf(
            GetDefaultMutator<IEcho_Echo_InputParams>()
        );
    }

// Output variants (all possible output parameter combinations)
// Variant containing all possible output parameter combinations for interface IEcho
    using IEcho_AllOutputParams = std::variant<IEcho_Echo_OutputParams>;

    // Mutator for the variant
    template<>
    auto GetDefaultMutator<IEcho_AllOutputParams>() {
        return fuzztest::VariantOf(
            GetDefaultMutator<IEcho_Echo_OutputParams>()
        );
    }

// Interface dispatcher functions
// Dispatcher function for interface IEcho
    // Calls the appropriate method based on the variant index
    void Dispatch(kosipc::stdcpp::test::IEcho& interface,
                  IEcho_AllInputParams& input_variant,
                  IEcho_AllOutputParams& output_variant) {
        switch (input_variant.index()) {
            case 0: {
                auto& inputParams = std::get<0>(input_variant);
                IEcho_Echo_OutputParams outputParams;
                interface.Echo(inputParams.input, outputParams.output);
                output_variant = outputParams;
                break;
            }
            default:
                __builtin_unreachable();
        }
    }

/////

using namespace std::chrono_literals;

// class EchoIpcFixture
// {
// public:
//     EchoIpcFixture()
//         : m_app(kosipc::MakeApplicationPureClient())
//         , m_proxy(m_app.MakeProxy<kosipc::stdcpp::test::IEcho>(kosipc::ConnectDcmPublication()))
//     {
//     }

//     void Echo(kosipc::stdcpp::test::TestStructureBig input)
//     {
//         kosipc::stdcpp::test::TestStructureBig result = input;
//         m_proxy->Echo(input, result);
//         EXPECT_EQ(input.param1.param1, result.param1.param1);
//         EXPECT_EQ(input.param1.param2, result.param1.param2);
//         EXPECT_EQ(input.param2, result.param2);
//     }

//     kosipc::Application m_app;
//     kosipc::unique_ptr<kosipc::stdcpp::test::IEcho> m_proxy;
// };
// FUZZ_TEST_F(EchoIpcFixture, Echo)
//     .WithDomains(GetDefaultMutator<kosipc::stdcpp::test::TestStructureBig>());

void TestEchoIpc(IEcho_AllInputParams input)
{

    if (auto* params = std::get_if<IEcho_Echo_InputParams>(&input)) {
        std::cerr << "Input param1: " << params->input.param1.param1
                  << ", param2: " << params->input.param2 << std::endl;
    }

    kosipc::Application app = kosipc::MakeApplicationPureClient();

    auto proxy = app.MakeProxy<kosipc::stdcpp::test::IEcho>(kosipc::ConnectDcmPublication());
    IEcho_AllOutputParams output;

    Dispatch(
        *proxy,
        input,
        output);

    coverage_mapper::Print();

    // proxy->Echo(input, output);

    // EXPECT_EQ(input.param1.param1, result.param1.param1);
    // EXPECT_EQ(input.param1.param2, result.param1.param2);
    // EXPECT_EQ(input.param2, result.param2);
}
FUZZ_TEST(IPC, TestEchoIpc)
    .WithDomains(GetDefaultMutator<IEcho_AllInputParams>())
    .WithSeeds({0});


// void TestEchoLocal(uint32_t i)
// {
//     // std::cerr << "LOCAL RUN " << i << '\n';
//     EXPECT_NE(i, 123);
// }
// FUZZ_TEST(LOCAL, TestEchoLocal)
//     .WithDomains(fuzztest::Positive<uint32_t>());

int main(int argc, char** argv) {

    kosipc::Application app = kosipc::MakeApplicationAutodetect();
    kosipc::components::Root root;

    coverage_mapper::RunCoverageMapperReciever(root.mapper, app);
    coverage_mapper::WaitCoverageReady();

    std::cerr << "START\n";

    char* custom_argv[] = {
        "my_fuzzer",
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
    coverage_mapper::Stop();
    return rc;
}
