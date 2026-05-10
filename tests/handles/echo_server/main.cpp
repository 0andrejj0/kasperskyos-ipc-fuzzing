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
#include <handle/handletype.h>

#include <exception>

namespace {

struct EchoImpl
    : public kosipc::stdcpp::test::IEcho
{
    void Register(nk_handle_desc_t& context) override
    {
        INFO(SERVER, "Register request");


        Handle outHandle = INVALID_HANDLE;
        auto rc = KnHandleCreateUserObject(HANDLE_TYPE_USER_FIRST, OCAP_HANDLE_TRANSFER, RTL_NULL, &outHandle);
        if (rc != rcOk)
        {
            ERR(SERVER, "Failed to create handle");
            throw std::runtime_error("error");
        }

        context = nk_handle_desc(outHandle);
    };

    void Read(const nk_handle_desc_t& context) override
    {
        auto raw_context = nk_get_handle(&context);
        if (raw_context != INVALID_HANDLE)
        {
            INFO(SERVER, "Read request: %u", context);
        }
        else
        {
            INFO(SERVER, "Read request: INVALID_HANDLE");
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
