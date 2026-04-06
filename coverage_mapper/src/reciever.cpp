#include "shared_memory_buffer.h"

#include <kl/CoverageMapper.cdl.cpp.h>

#include <kosipc/thread_pool.h>
#include <kosipc/serve_dynamic_channel.h>
#include <kosipc/api.h>

#include <kos/trace.h>

#include <rtl_cpp/retcode.h>

#include <atomic>
#include <iostream>

extern "C"
void __sanitizer_cov_8bit_counters_init(char* start, char* end);

namespace {

std::atomic<bool> ready{false};

class CoverageMapperRecieverImpl
    : public kosipc::stdcpp::kl::ICoverageMapper
{
public:
    void AddInline8BitCounters(Handle shmem, uint64_t shmemSize, uint64_t coverageStart, uint64_t coverageSize) override
    {
        std::cerr << "RECIEVED 8BIT MAPPING: " << shmem << ' ' << shmemSize << ' ' << coverageStart << ' ' << coverageSize << '\n';
        try
        {
            m_8bitCounters.emplace(shmem, shmemSize, coverageSize);
        }
        catch(const std::exception& e)
        {
            std::cerr << e.what();
            throw;
        }

        __sanitizer_cov_8bit_counters_init((char*)m_8bitCounters->GetData(), (char*)m_8bitCounters->GetData() + coverageSize);

        std::cerr << "8BIT MAPPING PROCESSED\n";
    }

    void Ready() override
    {
        std::cerr << "READY\n";
        ready = true;
        ready.notify_all();
    }

    std::optional<coverage_mapper::SharedMemoryBuffer> m_8bitCounters;
};

struct
{
    CoverageMapperRecieverImpl impl;
    std::vector<kosipc::EventLoop> eventLoops;
    kosipc::ServiceList endpoints;

    std::optional<kosipc::DcmServicePublisher> publisher;
    std::optional<kosipc::SimpleConnectionAcceptor> acceptor;

    std::vector<std::thread> threads;
} context;

} // namespace

namespace coverage_mapper {

kos::Result RunCoverageMapperReciever(kosipc::components::kl::CoverageMapper& component, kosipc::Application& app)
{
    INFO(COVERAGE, "RunCoverageMapperReciever()");

    component.mapper = &context.impl;

    context.eventLoops.emplace_back(app.MakeEventLoop(kosipc::ServeDynamicChannel(component)));

    context.endpoints.AddServices(component);

    context.publisher.emplace(app, context.endpoints);
    context.acceptor.emplace(app, context.endpoints);

    context.eventLoops.emplace_back(app.MakeEventLoop(kosipc::ServeConnectionRequests(&context.acceptor.value(), &context.publisher.value())));

    for (auto& eventLoop : context.eventLoops)
    {
        context.threads.emplace_back([&eventLoop](){
            eventLoop.Run();
        });
    }

    INFO(SERVER, "%s", "Coverage mapper stub created\n");

    return kos::Ok;
}

kos::Result WaitCoverageReady()
{
    ready.wait(false);
    return kos::Ok;
}

kos::Result Stop()
{
    return kos::Ok;
    for (auto& eventLoop: context.eventLoops)
    {
        eventLoop.RequestStop();
    }
    for (auto& thread: context.threads)
    {
        thread.join();
    }
}

} // namespace coverage_mapper


__attribute__((constructor))
void hello() {
    std::cerr << "HELLO FROM RECIEVER\n";
}
