#ifndef __BLUETOOTHCONNECTOR_HPP__
#define __BLUETOOTHCONNECTOR_HPP__
//Thanks Microsoft for the how-to https://github.com/microsoftarchive/msdn-code-gallery-microsoft/blob/master/Official%20Windows%20Platform%20Sample/Bluetooth%20connection%20sample/%5BC%2B%2B%5D-Bluetooth%20connection%20sample/C%2B%2B/bthcxn.cpp#L444


#include <string>
#include <winsock2.h>
#include <ws2bth.h>
#include <BluetoothAPIs.h>

#pragma comment(lib, "Bthprops.lib")
#pragma comment(lib, "Ws2_32.lib")

using namespace std;

#include "settings.hpp"

class BluetoothConnector
{
    public:
        BluetoothConnector(ServerSettings& settings);
        void startServer();

    private:
        const std::string uuid = "8a8478c9-2ca8-404b-a0 de-101f34ab71ae";
        const GUID guid = {0x8a8478c9, 0x2ca8, 0x404b, 0xa0, 0xde, 0x10, 0x1f, 0x34, 0xab, 0x71, 0xae};
        ServerSettings &settings;
        std::string getBluetoothDeviceName(int bluetoothAddress);

};

#endif
