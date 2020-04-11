#ifndef PACKIO_TESTS_MISC_H
#define PACKIO_TESTS_MISC_H

#include <atomic>
#include <chrono>
#include <future>

#include <gtest/gtest.h>

#include <packio/packio.h>

namespace packio {

template <typename endpoint>
endpoint get_endpoint();

template <>
inline packio::asio::ip::tcp::endpoint get_endpoint()
{
    return {packio::asio::ip::make_address("127.0.0.1"), 0};
}

#if defined(PACKIO_HAS_LOCAL_SOCKETS)
template <>
inline packio::asio::local::stream_protocol::endpoint get_endpoint()
{
    auto ts = std::chrono::system_clock::now().time_since_epoch().count();
    return {"/tmp/packio-" + std::to_string(ts)};
}
#endif // defined(PACKIO_HAS_LOCAL_SOCKETS)

class latch {
public:
    latch(int expected) : remaining_{expected} {}

    void count_down(int n = 1)
    {
        std::unique_lock lock{mutex_};
        remaining_ -= n;
        cv_.notify_all();
    }

    void count_up(int n = 1)
    {
        std::unique_lock lock{mutex_};
        remaining_ += n;
    }

    void reset(int n)
    {
        std::unique_lock lock{mutex_};
        remaining_ = n;
    }

    void wait()
    {
        std::unique_lock lock{mutex_};
        cv_.wait(lock, [this] { return remaining_ == 0; });
    }

    template <typename Duration>
    bool wait_for(Duration duration)
    {
        std::unique_lock lock{mutex_};
        return cv_.wait_for(lock, duration, [this] { return remaining_ == 0; });
    }

    template <typename Timepoint>
    bool wait_until(Timepoint timeout)
    {
        std::unique_lock lock{mutex_};
        return cv_.wait_until(lock, timeout, [this] { return remaining_ == 0; });
    }

private:
    mutable std::mutex mutex_;
    mutable std::condition_variable cv_;
    int remaining_;
};

} // packio

#endif // PACKIO_TESTS_MISC_H
