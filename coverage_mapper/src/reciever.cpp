#include <kl/CoverageMapper.cdl.cpp.h>

#include <kosipc/thread_pool.h>
#include <kosipc/serve_dynamic_channel.h>
#include <kosipc/api.h>

#include <kos/trace.h>

#include <rtl_cpp/retcode.h>

#include <iostream>

namespace {

class CoverageMapperRecieverImpl
    : public kosipc::stdcpp::kl::ICoverageMapper
{
public:
    void AddInline8BitCounters(Handle shmem, uint64_t shmemSize, uint64_t coverageStart, uint64_t coverageSize) override
    {
        std::cerr << "RECIEVED 8BIT MAPPING: " << shmem << ' ' << shmemSize << ' ' << coverageStart << ' ' << coverageSize << '\n';
    }

    void Ready() override
    {
        std::cerr << "READY\n";
    }
};

} // namespace

namespace coverage_mapper {

// kos::Result RunCoverageMapperReciever(kosipc::components::kl::CoverageMapper& component, kosipc::Application& app)
// {
//     CoverageMapperRecieverImpl impl;
//     component.mapper = &impl;

//     kosipc::ThreadPool tp(app);
//     tp.AddTask(kosipc::ServeDynamicChannel(component));

//     kosipc::ServiceList dynamicServices;
//     dynamicServices.AddServices(component.mapper);

//     kosipc::DcmServicePublisher publisher(app, dynamicServices);
//     kosipc::SimpleConnectionAcceptor acceptor(app, dynamicServices);

//     tp.AddTask(kosipc::ServeConnectionRequests(&acceptor, &publisher));

//     tp.Start();
//     std::cerr << "Coverage mapper stub created\n";

//     tp.Wait();
//     return kos::Ok;
// }

kos::Result RunCoverageMapperReciever(kosipc::components::kl::CoverageMapper& component, kosipc::Application& app)
{
    INFO(COVERAGE, "RunCoverageMapperReciever()");

    CoverageMapperRecieverImpl impl;
    component.mapper = &impl;

    std::vector<kosipc::EventLoop> eventLoops;
    eventLoops.emplace_back(app.MakeEventLoop(kosipc::ServeDynamicChannel(component)));

    kosipc::ServiceList endpoints;
    endpoints.AddServices(component);

    kosipc::DcmServicePublisher publisher(app, endpoints);
    kosipc::SimpleConnectionAcceptor acceptor(app, endpoints);

    eventLoops.emplace_back(app.MakeEventLoop(kosipc::ServeConnectionRequests(&acceptor, &publisher)));

    std::vector<std::thread> threads;
    for (auto& eventLoop : eventLoops)
    {
        threads.emplace_back([&eventLoop](){
            eventLoop.Run();
        });
    }

    INFO(SERVER, "%s", "Coverage mapper stub created\n");

    for (auto& t : threads)
    {
        t.join();
    }

    return kos::Ok;
}

} // namespace coverage_mapper


__attribute__((constructor))
void hello() {
    std::cerr << "HELLO FROM RECIEVER\n";
}
