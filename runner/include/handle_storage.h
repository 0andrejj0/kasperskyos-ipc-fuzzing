#pragma once

// ============================================================================
// handle_fuzz.h - Header-only helper for fuzzing KasperskyOS Handle types
// ============================================================================
//
// Purpose:
//   Provides simple functions to store, retrieve, and manage kernel handles
//   during fuzzing sessions. Handles are similar to file descriptors - numeric
//   identifiers that must be properly closed via KnHandleClose().
//
// Usage in generated fuzz code:
//   // When a method returns a Handle (out parameter):
//   StoreHandle(result_handle);
//
//   // When generating input for a Handle parameter:
//   Handle input = GetHandle();  // May return INVALID_HANDLE
//   interface.MethodWithHandle(input);
//
//   // When explicitly closing a handle:
//   RemoveHandle(handle_to_close);  // Calls KnHandleClose() internally
//
// Configuration (modify before first use if needed):
//   - kMaxStoredHandles: Max handles kept in pool (default: 10)
//   - kInvalidHandleProbability: Chance GetHandle() returns INVALID_HANDLE
//
// Thread safety: Thread-safe via std::mutex. Safe to use from multiple threads.
// ============================================================================

#include "common.h"

#include <fuzztest/fuzztest.h>

#include <coresrv/handle/handle_api.h>

#include <vector>
#include <random>
#include <algorithm>
#include <cstddef>
#include <mutex>
#include <string>

// ----------------------------------------------------------------------------
// Configuration constants - tweak these for your fuzzing needs
// ----------------------------------------------------------------------------
#ifndef HANDLE_FUZZ_MAX_STORED
#define HANDLE_FUZZ_MAX_STORED 10
#endif
constexpr std::size_t kMaxStoredHandles = HANDLE_FUZZ_MAX_STORED;

#ifndef HANDLE_FUZZ_INVALID_PROBABILITY
#define HANDLE_FUZZ_INVALID_PROBABILITY 0.15
#endif
constexpr double kInvalidHandleProbability = HANDLE_FUZZ_INVALID_PROBABILITY;

// ----------------------------------------------------------------------------
// Internal implementation (singleton pattern for global state)
// ----------------------------------------------------------------------------
class HandleStorage {
public:
    static void Store(Handle handle) {
        if (handle == INVALID_HANDLE) {
            return;
        }
        
        std::optional<Handle> to_close;  // Handle to close outside the lock
        
        {
            auto& self = Instance();
            std::lock_guard<std::mutex> lock(self.m_mutex);
            
            // Avoid storing duplicates
            if (std::find(self.m_pool.begin(), self.m_pool.end(), handle) 
                != self.m_pool.end()) {
                return;
            }
            
            // FIFO eviction if at capacity
            if (self.m_pool.size() >= kMaxStoredHandles) {
                to_close = self.m_pool.front();
                self.m_pool.erase(self.m_pool.begin());
            }
            
            // Add new handle
            self.m_pool.push_back(handle);
        }
        
        // Close evicted handle outside the lock (if any)
        if (to_close.has_value()) {
            KnHandleClose(to_close.value());
        }
    }
    
    /**
     * @brief Generate a Handle value for fuzzing input parameters
     * @return Random stored handle OR INVALID_HANDLE
     * 
     * Behavior:
     * - With probability kInvalidHandleProbability: returns INVALID_HANDLE
     * - If pool is empty: returns INVALID_HANDLE  
     * - Otherwise: returns uniformly random handle from stored pool
     * 
     * This allows fuzzing both valid handle usage and error paths with invalid handles.
     * Thread-safe.
     */
    static Handle Get() {
        auto& self = Instance();
        std::lock_guard<std::mutex> lock(self.m_mutex);
        
        // Return INVALID_HANDLE with configured probability
        std::uniform_real_distribution<double> prob_dist(0.0, 1.0);
        if (prob_dist(self.m_rng) < kInvalidHandleProbability) {
            return INVALID_HANDLE;
        }
        
        // No handles available to return
        if (self.m_pool.empty()) {
            return INVALID_HANDLE;
        }
        
        // Return random handle from pool
        std::uniform_int_distribution<std::size_t> idx_dist(0, self.m_pool.size() - 1);
        return self.m_pool[idx_dist(self.m_rng)];
    }
    
    /**
     * @brief Remove handle from pool and close it via kernel API
     * @param handle Handle to remove and close
     * 
     * Calls KnHandleClose(handle) if handle is valid and found in pool.
     * Safe to call with INVALID_HANDLE or non-existent handles (no-op).
     * Thread-safe.
     * 
     * Note: KnHandleClose is called while holding the mutex. If KnHandleClose
     * is not thread-safe or may block, consider external synchronization.
     */
    static void Remove(Handle handle) {
        if (handle == INVALID_HANDLE) {
            return;
        }
        
        auto& self = Instance();
        std::lock_guard<std::mutex> lock(self.m_mutex);
        
        auto it = std::find(self.m_pool.begin(), self.m_pool.end(), handle);
        
        if (it != self.m_pool.end()) {
            // Unlock before calling kernel function to avoid holding mutex
            // during potentially blocking operation
            lock.~lock_guard();
            
            KnHandleClose(handle);  // Kernel call to release resource
            
            // Re-lock to modify pool
            lock.~lock_guard();
            new (&lock) std::lock_guard<std::mutex>(self.m_mutex);
            
            // Re-find iterator since pool may have changed (in multithreaded env)
            it = std::find(self.m_pool.begin(), self.m_pool.end(), handle);
            if (it != self.m_pool.end()) {
                self.m_pool.erase(it);
            }
        }
    }
    
    /**
     * @brief Clear all stored handles and close them
     * 
     * Useful for test fixture teardown or between independent fuzz iterations.
     * Thread-safe.
     * 
     * Note: KnHandleClose is called while NOT holding the mutex to avoid
     * potential deadlocks if KnHandleClose blocks or calls back into fuzz code.
     */
    static void Clear() {
        std::vector<Handle> to_close;
        {
            auto& self = Instance();
            std::lock_guard<std::mutex> lock(self.m_mutex);
            to_close.swap(self.m_pool);  // Move contents, leaving pool empty
        }
        
        // Close handles outside the lock
        for (Handle h : to_close) {
            KnHandleClose(h);
        }
    }
    
    /**
     * @brief Get current count of stored handles (for debugging/metrics)
     * Thread-safe.
     */
    static std::size_t Count() {
        auto& self = Instance();
        std::lock_guard<std::mutex> lock(self.m_mutex);
        return self.m_pool.size();
    }
    
private:
    // Singleton accessor
    static HandleStorage& Instance() {
        static HandleStorage instance;
        return instance;
    }
    
    HandleStorage() : m_rng(std::random_device{}()) {}
    
    mutable std::mutex m_mutex;         // Protects m_pool and m_rng
    std::vector<Handle> m_pool;         // Stored valid handles
    std::mt19937 m_rng;                 // PRNG for random selection
};

// ============================================================================
// Public API - Free functions for use in generated fuzz code
// ============================================================================

/**
 * @brief Store a handle for future fuzzing use
 * @see HandleStorage::Store
 */
inline void StoreHandle(Handle handle) {
    HandleStorage::Store(handle);
}

/**
 * @brief Store a handle for future fuzzing use
 * @see HandleStorage::Store
 */
inline void StoreHandle(nk_handle_desc_t& handle) {
    HandleStorage::Store(nk_get_handle(&handle));
}

/**
 * @brief Get a handle value for fuzzing input parameters  
 * @see HandleStorage::Get
 */
inline Handle GetHandle() {
    return HandleStorage::Get();
}

/**
 * @brief Remove and close a handle
 * @see HandleStorage::Remove
 */
inline void RemoveHandle(Handle handle) {
    HandleStorage::Remove(handle);
}

// ----------------------------------------------------------------------------
// Optional utilities for advanced use cases
// ----------------------------------------------------------------------------

/**
 * @brief Clear all tracked handles and close them
 */
inline void ClearAllHandles() {
    HandleStorage::Clear();
}

/**
 * @brief Query current pool size (debugging/metrics)
 */
inline std::size_t GetStoredHandleCount() {
    return HandleStorage::Count();
}

/**
 * @brief RAII wrapper for automatic handle cleanup in fuzz tests
 * 
 * Example usage in generated mutator/dispatch code:
 *   ScopedHandle h(interface.MethodThatReturnsHandle());
 *   // h is automatically closed when going out of scope
 * 
 * Thread-safe for Store/Remove operations.
 */
class ScopedHandle {
public:
    ScopedHandle() : m_handle(INVALID_HANDLE) {}
    
    explicit ScopedHandle(Handle handle) : m_handle(handle) {
        if (m_handle != INVALID_HANDLE) {
            StoreHandle(m_handle);
        }
    }
    
    ~ScopedHandle() {
        reset();  // Ensure cleanup
    }
    
    // Non-copyable, movable
    ScopedHandle(const ScopedHandle&) = delete;
    ScopedHandle& operator=(const ScopedHandle&) = delete;
    
    ScopedHandle(ScopedHandle&& other) noexcept : m_handle(other.m_handle) {
        other.m_handle = INVALID_HANDLE;
    }
    
    ScopedHandle& operator=(ScopedHandle&& other) noexcept {
        if (this != &other) {
            reset();
            m_handle = other.m_handle;
            other.m_handle = INVALID_HANDLE;
        }
        return *this;
    }
    
    // Accessors
    Handle get() const { return m_handle; }
    
    Handle release() {
        Handle h = m_handle;
        m_handle = INVALID_HANDLE;
        return h;
    }
    
    void reset(Handle new_handle = INVALID_HANDLE) {
        if (m_handle != INVALID_HANDLE && m_handle != new_handle) {
            // Remove from tracking and close
            RemoveHandle(m_handle);  // Thread-safe
        }
        m_handle = new_handle;
        if (m_handle != INVALID_HANDLE) {
            StoreHandle(m_handle);   // Thread-safe
        }
    }
    
private:
    Handle m_handle;
};

auto HandleDomain = fuzztest::Map(
    [](int) { return GetHandle(); },
    fuzztest::Arbitrary<int>() 
);

template<>
auto GetDefaultMutator<nk_handle_desc_t>() {
    return fuzztest::Map(
        [](int) { return nk_handle_desc(GetHandle()); },
        fuzztest::Arbitrary<int>()
    );
}
