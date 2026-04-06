#pragma once

#include <coresrv/handle/handle_api.h>

namespace coverage_mapper {

class SharedMemoryBuffer
{
public:
    SharedMemoryBuffer(size_t size);
    SharedMemoryBuffer(Handle handle, size_t shmemSize, size_t dataSize);
    ~SharedMemoryBuffer();

public:
    Handle GetHandle();
    void* GetData();
    size_t GetSize();

private:
    Handle m_handle{INVALID_HANDLE};
    size_t m_size;
    void*  m_data;
};

} // namnespace coverage_mapper
