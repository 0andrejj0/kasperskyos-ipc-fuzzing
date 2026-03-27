#pragma once

#include <coresrv/handle/handle_api.h>

namespace coverage_mapper {

class SharedMemoryBuffer
{
public:
    SharedMemoryBuffer(size_t size);
    ~SharedMemoryBuffer();

public:
    Handle GetHandle();

private:
    Handle m_handle{INVALID_HANDLE};
};

} // namnespace coverage_mapper
