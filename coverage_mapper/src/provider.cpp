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

static std::optional<coverage_mapper::SharedMemoryBuffer> shmem_8bit_counters;

} // namespace

extern "C"
void __sanitizer_cov_trace_pc_guard_init(uint32_t *start, uint32_t *stop)
try
{
    ERR(COVERAGE, "Coverage init: %x, %x", (void*)start, (void*)stop);

    size_t coverageSize = stop - start;
    size_t shmemSize = AlignUp(coverageSize);

    auto shmem = coverage_mapper::SharedMemoryBuffer(shmemSize);

    // ERR(COVERAGE, "Coverage shmem: %x, %x", (void*)shmemStart, (void*)shmemEnd);

    shmem_8bit_counters.emplace(shmemSize);

    auto app = kosipc::MakeApplicationPureClient();
    std::optional<std::chrono::milliseconds> timeout = std::chrono::milliseconds{10'000};
    auto proxy = app.MakeProxy<kosipc::stdcpp::kl::ICoverageMapper>(kosipc::ConnectDcmPublication(std::nullopt, std::nullopt, std::nullopt, timeout, timeout));
    // auto proxy = app.MakeProxy<kosipc::stdcpp::kl::ICoverageMapper>(kosipc::ConnectDcmPublication());

    proxy->Ready();
    proxy->AddInline8BitCounters(INVALID_HANDLE, 1024, 1024, 1024);
}
catch (const std::exception& e)
{
    ERR(COVERAGE, "Coverage mapping failed: %s", e.what());
}

extern "C"
void __sanitizer_cov_trace_pc_guard(uint32_t *guard)
{

}

__attribute__((constructor))
void hello() {
    std::cerr << "HELLO FROM PROVIDER\n";
}
