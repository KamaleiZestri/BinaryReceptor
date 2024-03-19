#include <iostream>
#include <string>

#include "mode.hpp"
#include "starter.hpp"
#include "bluetooth.hpp"
#include "http.hpp"

using namespace std;

ConnectorStarter::ConnectorStarter(ServerSettings& settings) :settings(settings){}

void ConnectorStarter::startConnector()
{
    if (settings.mode == Mode::HTTP)
    {
        cout << "Starting HTTP mode...\n";
        startHttp();
    }
    else    //bluetooth mode
    {
        cout << "Starting Bluetooth mode...\n";
        startBluetooth();
    }
}

void ConnectorStarter::startBluetooth()
{
    BluetoothConnector blue = BluetoothConnector(settings);
    blue.startServer();
}

void ConnectorStarter::startHttp()
{
    HttpConnector http = HttpConnector(settings);
    http.startServer();
}
