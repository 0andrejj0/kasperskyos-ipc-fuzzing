#include <atomic>
#include <cstdint>
#include <utility>
#include <optional>

namespace {

} // namespace

// tested binary should be compiled with -fsanitize-coverage=trace-pc-guard
// and statically linked with this lib
namespace coverage_collector {

using CoverageMetric = double;

class CoverageCollector
{
public:
    CoverageCollector() = default;

    static CoverageCollector& GetInstance()
    {
        static CoverageCollector coverageCollector;
        return coverageCollector;
    }

    static const CoverageCollector& GetConstInstance()
    {
        return GetInstance();
    }
    
    CoverageMetric GetCurrentCoverage() const noexcept
    {
        return 0.0;
    }

    void InitCounters(uint32_t* start, uint32_t* stop) noexcept
    {
        if (!start || !stop || stop <= start)
        {
            for (auto it = start; it < stop; ++it)
            {
                *it = 0;
            }
        }

        m_guardCountersRange = std::make_pair(start, stop);
    }

    void TriggerCounter(uint32_t* guard)
    {
        auto* atomicGuard = reinterpret_cast<std::atomic<uint32_t>*>(guard);
        if (atomicGuard->exchange(1) == 0)
        {
            ++m_coveredTotal;
        }
    }

private:
    std::optional<std::pair<uint32_t*, uint32_t*>> m_guardCountersRange;
    std::atomic<size_t> m_coveredTotal = 0;
};

} // namespace coverage_collector

extern "C" {
    void __sanitizer_cov_trace_pc_guard_init(uint32_t* start, uint32_t* stop);
    void __sanitizer_cov_trace_pc_guard(uint32_t* guard);

    // TODO counter -> source mapping and report writing
    // void __sanitizer_cov_pcs_init(const uintptr_t* pcs_beg, const uintptr_t* pcs_end);
}

extern "C" void __sanitizer_cov_trace_pc_guard_init(uint32_t* start, uint32_t* stop)
{
    coverage_collector::CoverageCollector::GetInstance().InitCounters(start, stop);
}

extern "C" void __sanitizer_cov_trace_pc_guard(uint32_t* guard)
{
    coverage_collector::CoverageCollector::GetInstance().TriggerCounter(guard);
}
