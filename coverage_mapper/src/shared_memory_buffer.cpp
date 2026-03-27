#include "shared_memory_buffer.h"

#include <coresrv/vmm/vmm_api.h>

#define FMT_HEADER_ONLY
#include <fmt/format.h>

#include <rtl_cpp/retcode.h>
#include <rtl_cpp/retcode_hr.h>

#include <iostream>
#include <stdexcept>

namespace coverage_mapper {

SharedMemoryBuffer::SharedMemoryBuffer(size_t size)
{
    const auto rc = TO_RESULT(KnPmmMdlCreate(size, VMM_FLAG_READ, &m_handle));
    // const auto rc = TO_RESULT(KnPmmMdlCreate(size, VMM_FLAG_READ | VMM_FLAG_WRITE, &m_handle));
    if (kos::Bad(rc))
    {
        throw std::runtime_error(fmt::format("Failed to create shared memory buffer: {}", fmt::to_string(rc)));
    }
}

SharedMemoryBuffer::~SharedMemoryBuffer()
{
    KnHandleClose(m_handle);
}

Handle SharedMemoryBuffer::GetHandle()
{
    return m_handle;
}

} // namnespace coverage_mapper
