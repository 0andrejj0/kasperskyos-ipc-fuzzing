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

#include <exception>
#include <string>
#include <variant>

namespace {

static const std::string base64_chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789+/";

std::string base64_encode(const std::string &input) {
    std::string output;
    int val = 0, valb = -6;
    for (unsigned char c : input) {
        val = (val << 8) + c;
        valb += 8;
        while (valb >= 0) {
            output.push_back(base64_chars[(val >> valb) & 0x3F]);
            valb -= 6;
        }
    }
    if (valb > -6) {
        output.push_back(base64_chars[((val << 8) >> (valb + 8)) & 0x3F]);
    }
    while (output.size() % 4) {
        output.push_back('=');
    }
    return output;
}

struct EchoImpl
    : public kosipc::stdcpp::test::IEcho
{
    void Method1(int8_t input) override
    {
        INFO(SERVER, "Method1 request: %d", input);
        // OK
    }

    void Method2(uint32_t input) override
    {
        INFO(SERVER, "Method2 request: %d", input);
        // ok
    }

    void Method3(const TestStruct& input) override
    {
        std::string b64str = base64_encode(input.TestStructName);
        INFO(SERVER, "Method3 request: TestStruct{str:(size:%zu base64:%s), %d, bytes:(size:%zu)}", input.TestStructName.size(), b64str.c_str(), input.TestStructID, input.TestStructData.size());
        // ok
    }

    void Method4(const TestUnion& input) override
    {
        switch (input.index()) {
            case 0: {
                auto& inputParams = std::get<0>(input);
                // optional SimpleStruct
                if (inputParams.empty())
                {
                    INFO(SERVER, "Method4 request: TestUnion(0){}");
                }
                else
                {
                    INFO(SERVER, "Method4 request: TestUnion(0){SimpleStruct %d}", inputParams[0].c);
                }
                break;
            }
        case 1: {
                auto& inputParams = std::get<1>(input);
                INFO(SERVER, "Method4 request: TestUnion(1){%u}", inputParams);
                break;
            }
        default:
            __builtin_unreachable();
        }
    }

    void Method5(const TestStructWithArray& input) override
    {
        INFO(SERVER, "Method5 request: TestStructWithArray{[%d, %d, %d]}", input.arr[0], input.arr[1], input.arr[2]);
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
