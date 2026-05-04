#include "shared_memory_buffer.h"

#include <kl/ICoverageMapper.idl.cpp.h>

#include <kosipc/application.h>
#include <kosipc/connect_dcm_publication.h>
#include <kosipc/api.h>

#include <rtl_cpp/retcode.h>
#include <rtl_cpp/retcode_hr.h>

#include <rtl/align.h>
#include <hal/page.h>
#include <kos/trace.h>
#include <coresrv/vmm/vmm_api.h>

#define FMT_HEADER_ONLY
#include <fmt/format.h>

#include <chrono>
#include <iostream>
#include <optional>

namespace {

size_t AlignUp(size_t size)
{
    if (size % PAGE_SIZE != 0)
    {
        size += PAGE_SIZE - (size % PAGE_SIZE);
    }
    return size;
}

std::optional<coverage_mapper::SharedMemoryBuffer> shmem_8bit_counters;
uint32_t* pc_guard_start = 0;
uint32_t* pc_guard_stop = 0;

} // namespace

extern "C"
void __sanitizer_cov_trace_pc_guard_init(uint32_t* start, uint32_t* stop)
try
{
    pc_guard_start = start;
    pc_guard_stop = stop;
    ERR(COVERAGE, "Coverage init: %x, %x", (void*)start, (void*)stop);

    size_t coverageSize = stop - start;
    size_t shmemSize = AlignUp(coverageSize);

    shmem_8bit_counters.emplace(shmemSize);

    auto app = kosipc::MakeApplicationPureClient();
    std::optional<std::chrono::milliseconds> timeout = std::chrono::milliseconds{10'000};
    auto proxy = app.MakeProxy<kosipc::stdcpp::kl::ICoverageMapper>(kosipc::ConnectDcmPublication(std::nullopt, std::nullopt, std::nullopt, timeout, timeout));

    proxy->Add_88BitCounters(shmem_8bit_counters->GetHandle(), shmem_8bit_counters->GetSize(), 0, coverageSize);
    proxy->Ready();
}
catch (const std::exception& e)
{
    ERR(COVERAGE, "Coverage mapping failed: %s", e.what());
}

extern "C"
void __sanitizer_cov_trace_pc_guard(uint32_t* guard)
{
    size_t idx = guard - pc_guard_start;
    char* counter = (char*)shmem_8bit_counters->GetData() + idx;
    if (*counter != 128)
        ++*counter;
    // ERR(COVERAGE, "SET COVERAGE %d", idx);
}

__attribute__((constructor))
void hello() {
    std::cerr << "HELLO FROM PROVIDER\n";
}
