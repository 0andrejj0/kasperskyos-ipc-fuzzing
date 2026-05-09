#include "test/Echo.edl.cpp.h"
#include "test/IEcho.idl.cpp.h"

#include <exception>
#include <kosipc/application.h>
#include <kosipc/event_loop.h>
#include <kosipc/make_application.h>
#include <kosipc/root_component.h>
#include <kosipc/serve_dynamic_channel.h>
#include <kosipc/simple_connection_acceptor.h>
#include <kosipc/dcm_service_publisher.h>
#include <kosipc/thread_pool.h>
#include <kosipc/api.h>

#include <kos/trace.h>

namespace {

__attribute__((noinline))
void trigger_asan() {
    int* arr = new int[10];
    arr[10] = 42;
    delete[] arr;
}

struct EchoImpl
    : public kosipc::stdcpp::test::IEcho
{
    void Echo(const kosipc::stdcpp::test::TestStructure& input, kosipc::stdcpp::test::TestStructure& output) override
    {
        INFO(SERVER, "Echo request: %lu %u", input.param1, input.param2);
        if (input.param1 > 10)
        {
            output = input;
        }
        else
        {
            // error
            ERR(SERVER, "Error happens (asan)");
            trigger_asan();
            output = {};
        }
    }
};

} // namespace

int main() {
    INFO(SERVER, "%s", "Starting echo server\n");

    kosipc::Application app = kosipc::MakeApplicationAutodetect();

    kosipc::components::Root root;
    EchoImpl echoImpl;
    root.echo = &echoImpl;

    std::vector<kosipc::EventLoop> eventLoops;
    eventLoops.emplace_back(app.MakeEventLoop(ServeDynamicChannel(root)));

    kosipc::ServiceList endpoints;
    endpoints.AddServices(root.echo);

    kosipc::DcmServicePublisher publisher(app, endpoints);
    kosipc::SimpleConnectionAcceptor acceptor(app, endpoints);

    eventLoops.emplace_back(app.MakeEventLoop(ServeConnectionRequests(&acceptor, &publisher)));

    std::vector<std::thread> threads;
    for (auto& eventLoop : eventLoops)
    {
        threads.emplace_back([&eventLoop](){
            eventLoop.Run();
        });
    }

    ERR(SERVER, "%s", "Echo server started");

    for (auto& t : threads)
    {
        t.join();
    }

    return EXIT_SUCCESS;
}
