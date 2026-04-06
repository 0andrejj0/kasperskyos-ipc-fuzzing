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
    auto rc = TO_RESULT(KnPmmMdlCreate(size, VMM_FLAG_READ | VMM_FLAG_WRITE, &m_handle));
    if (kos::Bad(rc))
    {
        throw std::runtime_error(fmt::format("Failed to create shared memory buffer: {}", fmt::to_string(rc)));
    }

    void* data;
    rc = TO_RESULT(KnPmmMdlMap(m_handle, 0, size, RTL_NULL, VMM_FLAG_READ | VMM_FLAG_WRITE, &data));
    if (kos::Bad(rc))
    {
        KnHandleClose(m_handle);
        throw std::runtime_error(fmt::format("Failed to map shared memory buffer: {}", fmt::to_string(rc)));
    }

    m_data = data;
    m_size = size;
}

SharedMemoryBuffer::SharedMemoryBuffer(Handle handle, size_t shmemSize, size_t dataSize)
{
    m_handle = handle;
    void* data;
    auto rc = TO_RESULT(KnPmmMdlMap(m_handle, 0, shmemSize, RTL_NULL, VMM_FLAG_READ | VMM_FLAG_WRITE, &data));
    if (kos::Bad(rc))
    {
        throw std::runtime_error(fmt::format("Failed to map shared memory buffer: {}", fmt::to_string(rc)));
    }
    m_data = data;
    m_size = dataSize;
}

SharedMemoryBuffer::~SharedMemoryBuffer()
{
    KnHandleClose(m_handle);
}

Handle SharedMemoryBuffer::GetHandle()
{
    return m_handle;
}

void* SharedMemoryBuffer::GetData()
{
    return m_data;
}

size_t SharedMemoryBuffer::GetSize()
{
    return m_size;
}

} // namnespace coverage_mapper
