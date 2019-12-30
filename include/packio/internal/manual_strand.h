// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

#ifndef PACKIO_MANUAL_STRAND_H
#define PACKIO_MANUAL_STRAND_H

#include <queue>
#include <boost/asio.hpp>

namespace packio {
namespace internal {

template <typename Executor>
class manual_strand {
public:
    using function_type = std::function<void()>;

    manual_strand(const Executor& executor) : strand_{executor} {}

    void push(function_type function)
    {
        boost::asio::dispatch(
            strand_, [this, function = std::move(function)]() mutable {
                queue_.push(std::move(function));

                if (!executing_) {
                    executing_ = true;
                    execute();
                }
            });
    }

    void next()
    {
        boost::asio::dispatch(strand_, [this] { execute(); });
    }

private:
    void execute()
    {
        if (queue_.empty()) {
            executing_ = false;
            return;
        }

        queue_.front()();
        queue_.pop();
    }

    boost::asio::strand<Executor> strand_;
    std::queue<function_type> queue_;
    bool executing_{false};
};

} // internal
} // packio

#endif // PACKIO_MANUAL_STRAND_H