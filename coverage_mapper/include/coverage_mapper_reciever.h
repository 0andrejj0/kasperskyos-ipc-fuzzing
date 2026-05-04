#pragma once

#include <kl/CoverageMapper.cdl.cpp.h>

#include <kosipc/application.h>

#include <rtl_cpp/retcode.h>

namespace coverage_mapper {

kos::Result RunCoverageMapperReciever(kosipc::components::kl::CoverageMapper& component, kosipc::Application& app);

kos::Result WaitCoverageReady();

kos::Result Stop();

void Print();

} // namespace coverage_mapper
