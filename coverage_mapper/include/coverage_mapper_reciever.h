#pragma once

#include <kl/CoverageMapper.cdl.cpp.h>

#include <kosipc/application.h>

#include <rtl_cpp/retcode.h>

namespace coverage_mapper {

kos::Result RunCoverageMapperReciever(kosipc::components::kl::CoverageMapper& component, kosipc::Application& app);

} // namespace coverage_mapper
