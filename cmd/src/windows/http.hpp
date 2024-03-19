#ifndef __HTTPCONNECTOR_HPP__
#define __HTTPCONNECTOR_HPP__

#include <winsock2.h>

#pragma comment(lib, "Ws2_32.lib")

#include "settings.hpp"

class HttpConnector
{
    public:
        HttpConnector(ServerSettings& settings);
        void startServer();
    
    private:
        ServerSettings &settings;
};

#endif
