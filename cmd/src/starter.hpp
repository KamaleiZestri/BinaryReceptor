#ifndef __STARTER_HPP__
#define __STARTER_HPP__

#include "mode.hpp"
#include "settings.hpp"

class ConnectorStarter
{
    public:
        ConnectorStarter(ServerSettings& settings);
        void startConnector();

    private:
        ServerSettings &settings;
        void startBluetooth();
        void startHttp();
};

#endif
