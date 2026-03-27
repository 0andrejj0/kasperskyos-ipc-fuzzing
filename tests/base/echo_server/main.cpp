#include "test/Echo.edl.cpp.h"
#include "test/IEcho.idl.cpp.h"

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

struct EchoImpl
    : public kosipc::stdcpp::test::IEcho
{
    void Echo(uint32_t input, uint32_t& output) override
    {
        ERR(SERVER, "REQUEST: %u", input);
        if (input != 123)
        {
            output = input;
        }
        else
        {
            // error
            output = 1;
        }
    }
};

} // namespace

int main() {
    INFO(SERVER, "%s", "HELLO FROM ECHO SERVER)))\n");

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

    ERR(SERVER, "%s", "ECHO SERVER STARTED)))");

    for (auto& t : threads)
    {
        t.join();
    }

    return EXIT_SUCCESS;
}
