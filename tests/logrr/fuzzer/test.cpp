// #include "generated_fuzztest.h"

// Auto-generated mutators for IDL interfaces

#include<fuzztest/fuzztest.h>
#include<fuzztest/googletest_adaptor.h>
#include<fuzztest/googletest_fixture_adapter.h>
#include<gtest/gtest.h>

#include<testing/common.h>
#include<testing/handle_storage.h>

#include<kl/CoverageMapper.cdl.cpp.h>
#include<component/coverage_mapper/coverage_mapper_reciever.h>

#include<kosipc/application.h>
#include<kosipc/connect_dcm_publication.h>
#include<kosipc/api.h>

#include<kos/trace.h>

#include<kl/core/Types.idl.cpp.h>
#include<kl/core/Thread.idl.cpp.h>
#include<logrr/Types.idl.cpp.h>
#include<logrr/LogProvider.idl.cpp.h>

// Packages: kl.core.Types, kl.core.Thread, logrr.Types, logrr.LogProvider

auto ascii_char = fuzztest::InRange<char>(0, 127);
// Type definitions resolution:
// Char -> UInt8
// Boolean -> UInt8
// SizeT -> UInt64
// TrRetcode -> SInt32
// UCoreString -> string<1023>
// ExecutableBuildId -> sequence
// TimeUnit -> UInt64
// Uuid -> array
// Routine -> UInt64
// TrTid -> UInt32
// HandleRights -> UInt32
// NkResult -> SInt32
// Error -> SInt32
// QueueMaxSizeInBytes -> UInt32
// FragmentId -> UInt32
// FileName -> string<1024>
// LogPayload -> string<128>
// FunctionName -> string<64>
// LogLevel -> SInt8
// ProviderName -> string<1023>
// SubProviderId -> UInt16
// ChannelName -> string<1023>
// Bool -> UInt8
// LogEntries -> sequence
// SubProvidersConfigById -> sequence

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
// Mutator for union TrSchedParam
template<>
auto GetDefaultMutator<kosipc::stdcpp::kl::core::TrSchedParam>() {
    return fuzztest::VariantOf(
        GetDefaultMutator<kosipc::stdcpp::kl::core::TrNoneParam>() /* none */,
        GetDefaultMutator<kosipc::stdcpp::kl::core::TrRoundRobinParam>() /* rr */
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
// Mutator for struct TrThreadInfo
template<>
auto GetDefaultMutator<kosipc::stdcpp::kl::core::TrThreadInfo>() {
    return fuzztest::StructOf<kosipc::stdcpp::kl::core::TrThreadInfo>(
        fuzztest::Arbitrary<uint64_t>() /* stackSize */,
        fuzztest::Arbitrary<uint64_t>() /* stackStart */,
        fuzztest::Arbitrary<uint32_t>() /* tid */,
        fuzztest::Arbitrary<uint64_t>() /* tls */
    );
}
// Mutator for struct GeneralLogEntryBase
template<>
auto GetDefaultMutator<kosipc::stdcpp::logrr::GeneralLogEntryBase>() {
    return fuzztest::StructOf<kosipc::stdcpp::logrr::GeneralLogEntryBase>(
        fuzztest::Arbitrary<uint8_t>() /* messageIncomplete */,
        fuzztest::ContainerOf<std::string>(ascii_char).WithMaxSize(128) /* message */
    );
}
// Mutator for struct GeneralLogEntry
template<>
auto GetDefaultMutator<kosipc::stdcpp::logrr::GeneralLogEntry>() {
    return fuzztest::StructOf<kosipc::stdcpp::logrr::GeneralLogEntry>(
        fuzztest::Arbitrary<int32_t>() /* pid */,
        fuzztest::Arbitrary<int32_t>() /* tid */,
        fuzztest::Arbitrary<uint32_t>() /* line */,
        GetDefaultMutator<kosipc::stdcpp::kl::core::TimeSpec>() /* timestamp */,
        GetDefaultMutator<kosipc::stdcpp::kl::core::TimeSpec>() /* steadyTimestamp */,
        fuzztest::Arbitrary<int8_t>() /* level */,
        fuzztest::ContainerOf<std::string>(ascii_char).WithMaxSize(1024) /* file */,
        fuzztest::ContainerOf<std::string>(ascii_char).WithMaxSize(64) /* function */,
        GetDefaultMutator<kosipc::stdcpp::logrr::GeneralLogEntryBase>() /* base */
    );
}
// Mutator for union LogEntry
template<>
auto GetDefaultMutator<kosipc::stdcpp::logrr::LogEntry>() {
    return fuzztest::VariantOf(
        GetDefaultMutator<kosipc::stdcpp::logrr::GeneralLogEntryBase>() /* base */,
        GetDefaultMutator<kosipc::stdcpp::logrr::GeneralLogEntry>() /* general */
    );
}
// Mutator for struct LogsBufferingOpts
template<>
auto GetDefaultMutator<kosipc::stdcpp::logrr::LogsBufferingOpts>() {
    return fuzztest::StructOf<kosipc::stdcpp::logrr::LogsBufferingOpts>(
        fuzztest::Arbitrary<uint32_t>() /* batchSize */,
        fuzztest::Arbitrary<uint32_t>() /* accumulateTimeoutMs */
    );
}
// Mutator for struct ProviderConfig
template<>
auto GetDefaultMutator<kosipc::stdcpp::logrr::ProviderConfig>() {
    return fuzztest::StructOf<kosipc::stdcpp::logrr::ProviderConfig>(
        fuzztest::Arbitrary<int8_t>() /* logLevel */,
        fuzztest::Arbitrary<uint32_t>() /* queueMaxSizeInBytes */,
        GetDefaultMutator<kosipc::stdcpp::logrr::LogsBufferingOpts>() /* bufferingOpts */
    );
}
// Mutator for struct SubProviderConfig
template<>
auto GetDefaultMutator<kosipc::stdcpp::logrr::SubProviderConfig>() {
    return fuzztest::StructOf<kosipc::stdcpp::logrr::SubProviderConfig>(
        fuzztest::Arbitrary<int8_t>() /* logLevel */
    );
}
// Mutator for struct ProviderLogEntry
template<>
auto GetDefaultMutator<kosipc::stdcpp::logrr::ProviderLogEntry>() {
    return fuzztest::StructOf<kosipc::stdcpp::logrr::ProviderLogEntry>(
        fuzztest::Arbitrary<uint16_t>() /* subProviderId */,
        fuzztest::Arbitrary<uint32_t>() /* fragmentId */,
        GetDefaultMutator<kosipc::stdcpp::logrr::LogEntry>() /* logEntry */
    );
}
// Mutator for struct SubProviderConfigByIdPair
template<>
auto GetDefaultMutator<kosipc::stdcpp::logrr::SubProviderConfigByIdPair>() {
    return fuzztest::StructOf<kosipc::stdcpp::logrr::SubProviderConfigByIdPair>(
        fuzztest::Arbitrary<uint16_t>() /* subProviderId */,
        GetDefaultMutator<kosipc::stdcpp::logrr::SubProviderConfig>() /* config */
    );
}

// Input parameter structures for interface methods
// Input parameters structure for LogProvider::RegisterProviderByName
struct LogProvider_RegisterProviderByName_InputParams {
    kosipc::stdcpp::logrr::ProviderName name;
};
// Mutator for input params of LogProvider::RegisterProviderByName
template<>
auto GetDefaultMutator<LogProvider_RegisterProviderByName_InputParams>() {
    return fuzztest::StructOf<LogProvider_RegisterProviderByName_InputParams>(
        fuzztest::ContainerOf<std::string>(ascii_char).WithMaxSize(1023) /* name */
    );
}
// Input parameters structure for LogProvider::RegisterSubProvider
struct LogProvider_RegisterSubProvider_InputParams {
    nk_handle_desc_t providerHandle;
    kosipc::stdcpp::logrr::ProviderName subProviderName;
};
// Mutator for input params of LogProvider::RegisterSubProvider
template<>
auto GetDefaultMutator<LogProvider_RegisterSubProvider_InputParams>() {
    return fuzztest::StructOf<LogProvider_RegisterSubProvider_InputParams>(
        GetDefaultMutator<nk_handle_desc_t>() /* providerHandle */,
        fuzztest::ContainerOf<std::string>(ascii_char).WithMaxSize(1023) /* subProviderName */
    );
}
// Input parameters structure for LogProvider::Log
struct LogProvider_Log_InputParams {
    nk_handle_desc_t providerHandle;
    kosipc::stdcpp::logrr::LogEntries entries;
};
// Mutator for input params of LogProvider::Log
template<>
auto GetDefaultMutator<LogProvider_Log_InputParams>() {
    return fuzztest::StructOf<LogProvider_Log_InputParams>(
        GetDefaultMutator<nk_handle_desc_t>() /* providerHandle */,
        fuzztest::VectorOf(GetDefaultMutator<kosipc::stdcpp::logrr::ProviderLogEntry>()).WithMaxSize(64) /* entries */
    );
}
// Input parameters structure for LogProvider::GetConfig
struct LogProvider_GetConfig_InputParams {
    nk_handle_desc_t providerHandle;
};
// Mutator for input params of LogProvider::GetConfig
template<>
auto GetDefaultMutator<LogProvider_GetConfig_InputParams>() {
    return fuzztest::StructOf<LogProvider_GetConfig_InputParams>(
        GetDefaultMutator<nk_handle_desc_t>() /* providerHandle */
    );
}
// Input parameters structure for LogProvider::ConfirmConfigApplied
struct LogProvider_ConfirmConfigApplied_InputParams {
    nk_handle_desc_t providerHandle;
    kosipc::stdcpp::logrr::Error configApplicationResult;
};
// Mutator for input params of LogProvider::ConfirmConfigApplied
template<>
auto GetDefaultMutator<LogProvider_ConfirmConfigApplied_InputParams>() {
    return fuzztest::StructOf<LogProvider_ConfirmConfigApplied_InputParams>(
        GetDefaultMutator<nk_handle_desc_t>() /* providerHandle */,
        fuzztest::Arbitrary<int32_t>() /* configApplicationResult */
    );
}

// Output parameter structures for interface methods
// Output parameters structure for LogProvider::RegisterProviderByName
struct LogProvider_RegisterProviderByName_OutputParams {
    nk_handle_desc_t providerHandle;
    kosipc::stdcpp::logrr::ProviderConfig initialConfig;
    kosipc::stdcpp::logrr::Bool writeToCore;
    kosipc::stdcpp::logrr::Bool markCoreLogs;
};
// Mutator for output params of LogProvider::RegisterProviderByName
template<>
auto GetDefaultMutator<LogProvider_RegisterProviderByName_OutputParams>() {
    return fuzztest::StructOf<LogProvider_RegisterProviderByName_OutputParams>(
        GetDefaultMutator<nk_handle_desc_t>() /* providerHandle */,
        GetDefaultMutator<kosipc::stdcpp::logrr::ProviderConfig>() /* initialConfig */,
        fuzztest::Arbitrary<uint8_t>() /* writeToCore */,
        fuzztest::Arbitrary<uint8_t>() /* markCoreLogs */
    );
}
// Output parameters structure for LogProvider::RegisterSubProvider
struct LogProvider_RegisterSubProvider_OutputParams {
    kosipc::stdcpp::logrr::SubProviderId subProviderId;
    kosipc::stdcpp::logrr::SubProviderConfig initialConfig;
};
// Mutator for output params of LogProvider::RegisterSubProvider
template<>
auto GetDefaultMutator<LogProvider_RegisterSubProvider_OutputParams>() {
    return fuzztest::StructOf<LogProvider_RegisterSubProvider_OutputParams>(
        fuzztest::Arbitrary<uint16_t>() /* subProviderId */,
        GetDefaultMutator<kosipc::stdcpp::logrr::SubProviderConfig>() /* initialConfig */
    );
}
// Output parameters structure for LogProvider::Log
struct LogProvider_Log_OutputParams {
    // No output parameters
};
// Mutator for output params of LogProvider::Log
template<>
auto GetDefaultMutator<LogProvider_Log_OutputParams>() {
    return fuzztest::StructOf<LogProvider_Log_OutputParams>(
        // No output parameters
    );
}
// Output parameters structure for LogProvider::GetConfig
struct LogProvider_GetConfig_OutputParams {
    kosipc::stdcpp::logrr::ProviderConfig config;
    kosipc::stdcpp::logrr::SubProvidersConfigById subProvidersConfig;
};
// Mutator for output params of LogProvider::GetConfig
template<>
auto GetDefaultMutator<LogProvider_GetConfig_OutputParams>() {
    return fuzztest::StructOf<LogProvider_GetConfig_OutputParams>(
        GetDefaultMutator<kosipc::stdcpp::logrr::ProviderConfig>() /* config */,
        fuzztest::VectorOf(GetDefaultMutator<kosipc::stdcpp::logrr::SubProviderConfigByIdPair>()).WithMaxSize(128) /* subProvidersConfig */
    );
}
// Output parameters structure for LogProvider::ConfirmConfigApplied
struct LogProvider_ConfirmConfigApplied_OutputParams {
    // No output parameters
};
// Mutator for output params of LogProvider::ConfirmConfigApplied
template<>
auto GetDefaultMutator<LogProvider_ConfirmConfigApplied_OutputParams>() {
    return fuzztest::StructOf<LogProvider_ConfirmConfigApplied_OutputParams>(
        // No output parameters
    );
}

// Input variants (all possible input parameter combinations)
// Variant containing all possible input parameter combinations for interface LogProvider
    using LogProvider_AllInputParams = std::variant<LogProvider_RegisterProviderByName_InputParams, LogProvider_RegisterSubProvider_InputParams, LogProvider_Log_InputParams, LogProvider_GetConfig_InputParams, LogProvider_ConfirmConfigApplied_InputParams>;

    // Mutator for the variant
    template<>
    auto GetDefaultMutator<LogProvider_AllInputParams>() {
        return fuzztest::VariantOf(
            GetDefaultMutator<LogProvider_RegisterProviderByName_InputParams>(),
        GetDefaultMutator<LogProvider_RegisterSubProvider_InputParams>(),
        GetDefaultMutator<LogProvider_Log_InputParams>(),
        GetDefaultMutator<LogProvider_GetConfig_InputParams>(),
        GetDefaultMutator<LogProvider_ConfirmConfigApplied_InputParams>()
        );
    }

// Output variants (all possible output parameter combinations)
// Variant containing all possible output parameter combinations for interface LogProvider
    using LogProvider_AllOutputParams = std::variant<LogProvider_RegisterProviderByName_OutputParams, LogProvider_RegisterSubProvider_OutputParams, LogProvider_Log_OutputParams, LogProvider_GetConfig_OutputParams, LogProvider_ConfirmConfigApplied_OutputParams>;

    // Mutator for the variant
    template<>
    auto GetDefaultMutator<LogProvider_AllOutputParams>() {
        return fuzztest::VariantOf(
            GetDefaultMutator<LogProvider_RegisterProviderByName_OutputParams>(),
        GetDefaultMutator<LogProvider_RegisterSubProvider_OutputParams>(),
        GetDefaultMutator<LogProvider_Log_OutputParams>(),
        GetDefaultMutator<LogProvider_GetConfig_OutputParams>(),
        GetDefaultMutator<LogProvider_ConfirmConfigApplied_OutputParams>()
        );
    }

// Interface dispatcher functions
// Dispatcher function for interface LogProvider
    // Calls the appropriate method based on the variant index
    void Dispatch(kosipc::stdcpp::logrr::LogProvider& interface,
                  LogProvider_AllInputParams& input_variant,
                  LogProvider_AllOutputParams& output_variant) {
        switch (input_variant.index()) {
            case 0: {
                    auto& inputParams = std::get<0>(input_variant);
                    LogProvider_RegisterProviderByName_OutputParams outputParams;
                    interface.RegisterProviderByName(inputParams.name, outputParams.providerHandle, outputParams.initialConfig, outputParams.writeToCore, outputParams.markCoreLogs);
                    StoreHandle(outputParams.providerHandle);
                    output_variant = outputParams;
                    break;
                }
        case 1: {
                    auto& inputParams = std::get<1>(input_variant);
                    LogProvider_RegisterSubProvider_OutputParams outputParams;
                    interface.RegisterSubProvider(inputParams.providerHandle, inputParams.subProviderName, outputParams.subProviderId, outputParams.initialConfig);
                    output_variant = outputParams;
                    break;
                }
        case 2: {
                    auto& inputParams = std::get<2>(input_variant);
                    LogProvider_Log_OutputParams outputParams;
                    interface.Log(inputParams.providerHandle, inputParams.entries);
                    output_variant = outputParams;
                    break;
                }
        case 3: {
                    auto& inputParams = std::get<3>(input_variant);
                    LogProvider_GetConfig_OutputParams outputParams;
                    interface.GetConfig(inputParams.providerHandle, outputParams.config, outputParams.subProvidersConfig);
                    output_variant = outputParams;
                    break;
                }
        case 4: {
                    auto& inputParams = std::get<4>(input_variant);
                    LogProvider_ConfirmConfigApplied_OutputParams outputParams;
                    interface.ConfirmConfigApplied(inputParams.providerHandle, inputParams.configApplicationResult);
                    output_variant = outputParams;
                    break;
                }
            default:
                __builtin_unreachable();
        }
    }

// Fuzz test fixtures
// Fuzz test fixture for interface LogProvider
    class LogProviderIpcFixture
    {
    public:
        LogProviderIpcFixture()
            : m_app(kosipc::MakeApplicationPureClient())
            , m_proxy(m_app.MakeProxy<kosipc::stdcpp::logrr::LogProvider>(kosipc::ConnectDcmPublication()))
        {}

        void Fuzz(LogProvider_AllInputParams input)
        {
            LogProvider_AllOutputParams output;

            try
            {
                coverage_mapper::AddFakeCoverage();
                Dispatch(
                    *m_proxy,
                    input,
                    output);
            }
            catch(const std::runtime_error& e)
            {
                std::string msg = e.what();
                const std::string prefix = "Transport error";
                
                if (msg.size() >= prefix.size() && 
                    msg.compare(0, prefix.size(), prefix) == 0) {
                    throw;
                }
            }
        }

        kosipc::Application m_app;
        kosipc::unique_ptr<kosipc::stdcpp::logrr::LogProvider> m_proxy;
    };

    FUZZ_TEST_F(LogProviderIpcFixture, Fuzz)
        .WithDomains(GetDefaultMutator<LogProvider_AllInputParams>());
