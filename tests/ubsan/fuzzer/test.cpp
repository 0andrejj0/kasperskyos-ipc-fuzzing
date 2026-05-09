#include "generated_fuzztest.h"

// class IEchoIpcFixture
// {
// public:
//     IEchoIpcFixture()
//         : m_app(kosipc::MakeApplicationPureClient())
//         , m_proxy(m_app.MakeProxy<kosipc::stdcpp::test::IEcho>(kosipc::ConnectDcmPublication()))
//     {
//     }

//     void Fuzz(IEcho_AllInputParams input)
//     {
//         IEcho_AllOutputParams output;

//         Dispatch(
//             *m_proxy,
//             input,
//             output);
//     }

//     kosipc::Application m_app;
//     kosipc::unique_ptr<kosipc::stdcpp::test::IEcho> m_proxy;
// };
// FUZZ_TEST_F(IEchoIpcFixture, Fuzz)
//     .WithDomains(GetDefaultMutator<IEcho_AllInputParams>());
