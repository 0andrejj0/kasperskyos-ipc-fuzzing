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
        INFO(COVERAGE, "Received 8-bit counters mapping: shmem=%p, shmemSize=%llu, coverageStart=0x%llx, coverageSize=%llu",
             shmem, shmemSize, coverageStart, coverageSize);

        try
        {
            m_8bitCounters.emplace(shmem, shmemSize, coverageSize);
            INFO(COVERAGE, "Shared memory buffer created successfully: size=%llu", coverageSize);
        }
        catch(const std::exception& e)
        {
            ERR(COVERAGE, "Failed to create shared memory buffer: %s", e.what());
            throw;
        }

        __sanitizer_cov_8bit_counters_init((char*)m_8bitCounters->GetData(), (char*)m_8bitCounters->GetData() + coverageSize);

        INFO(COVERAGE, "8-bit counters initialized: start=%p, end=%p",
             (void*)m_8bitCounters->GetData(),
             (void*)((char*)m_8bitCounters->GetData() + coverageSize));
    }

    void Ready() override
    {
        INFO(COVERAGE, "Coverage mapper ready signal received");
        ready = true;
        ready.notify_all();
    }

    void Print()
    {
        if (m_8bitCounters.has_value())
        {
            size_t totalCounters = m_8bitCounters->GetSize();
            size_t nonZeroCounters = 0;

            const char* data = (const char*)m_8bitCounters->GetData();

            for (size_t i = 0; i < totalCounters; ++i)
            {
                if (data[i] != 0)
                {
                    ++nonZeroCounters;
                }
            }

            int coveragePercent = (totalCounters > 0)
                        ? (nonZeroCounters * 100 / totalCounters)
                        : 0;

            int coveragePercentWithFraction = (totalCounters > 0)
                ? (nonZeroCounters * 1000 / totalCounters)
                : 0;

            INFO(COVERAGE, "Coverage statistics: total=%zu, covered=%zu, coverage=%d%% (%d.%d%%)",
                    totalCounters, nonZeroCounters,
                    coveragePercent,
                    coveragePercentWithFraction / 10,
                    coveragePercentWithFraction % 10);
        }
        else
        {
            WARN(COVERAGE, "No coverage counters available to print");
        }
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
    INFO(COVERAGE, "Starting coverage mapper receiver initialization");

    component.mapper = &context.impl;

    context.eventLoops.emplace_back(app.MakeEventLoop(kosipc::ServeDynamicChannel(component)));
    context.endpoints.AddServices(component);
    context.publisher.emplace(app, context.endpoints);
    context.acceptor.emplace(app, context.endpoints);
    context.eventLoops.emplace_back(app.MakeEventLoop(kosipc::ServeConnectionRequests(&context.acceptor.value(), &context.publisher.value())));

    INFO(COVERAGE, "Connection request event loop created");

    for (auto& eventLoop : context.eventLoops)
    {
        context.threads.emplace_back([&eventLoop](){
            eventLoop.Run();
        });
    }

    INFO(COVERAGE, "Coverage mapper stub created successfully with %zu threads", context.threads.size());

    return kos::Ok;
}

kos::Result WaitCoverageReady()
{
    INFO(COVERAGE, "Waiting for coverage mapper ready signal");
    ready.wait(false);
    INFO(COVERAGE, "Coverage mapper is ready");
    return kos::Ok;
}

kos::Result Stop()
{
    INFO(COVERAGE, "Stopping coverage mapper (cleanup in progress)");

    for (size_t i = 0; i < context.eventLoops.size(); ++i)
    {
        INFO(COVERAGE, "Requesting stop for event loop %zu", i);
        context.eventLoops[i].RequestStop();
    }

    for (size_t i = 0; i < context.threads.size(); ++i)
    {
        if (context.threads[i].joinable())
        {
            context.threads[i].join();
        }
        else
        {
            WARN(COVERAGE, "Thread %zu is not joinable", i);
        }
    }

    INFO(COVERAGE, "Coverage mapper stopped successfully");
    return kos::Ok;
}

void Print()
{
    INFO(COVERAGE, "Printing coverage mapper state");
    context.impl.Print();
}

} // namespace coverage_mapper
