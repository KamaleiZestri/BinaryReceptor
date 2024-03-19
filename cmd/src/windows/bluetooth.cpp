#include <iostream>

#include <winsock2.h>
#include <ws2bth.h>
#include <BluetoothAPIs.h>

#pragma comment(lib, "Bthprops.lib")
#pragma comment(lib, "Ws2_32.lib")

#include "bluetooth.hpp"
#include "keypress.hpp"
#include "util.hpp"

using namespace std;

BluetoothConnector::BluetoothConnector(ServerSettings& settings): settings(settings)
{
    WSADATA wsd;
    if (WSAStartup(MAKEWORD(2, 2), &wsd) != 0)
    {
        cout << "Unable to load WinSock version 2.2!";
    }
}

void BluetoothConnector::startServer()
{
    SOCKET blueSocket = socket(AF_BTH, SOCK_STREAM, BTHPROTO_RFCOMM);

    if (INVALID_SOCKET == blueSocket)
    {
        cout << "Socket is invalid. Please try again.\n";
        cout << WSAGetLastError();
        return;
    }

    SOCKADDR_BTH blueInfo = {0};
    blueInfo.addressFamily = AF_BTH;
    // blueInfo.serviceClassId = guid;
    // blueInfo.btAddr = 0; //dynamic
    blueInfo.port = BT_PORT_ANY; //also dynamic


    if (SOCKET_ERROR == bind(blueSocket, (struct sockaddr *) &blueInfo, sizeof(SOCKADDR_BTH)))
    {
        cout << "Error binding socket. Please try again.\n";
        cout << WSAGetLastError();
        return;
    }

    int addrlen = sizeof(SOCKADDR_BTH);
    getsockname(blueSocket, (struct sockaddr *) &blueInfo, &addrlen);

    CSADDR_INFO sockInfo;
    sockInfo.iProtocol = BTHPROTO_RFCOMM;
    sockInfo.iSocketType = SOCK_STREAM;
    sockInfo.LocalAddr.iSockaddrLength = sizeof(SOCKADDR_BTH);
    sockInfo.LocalAddr.lpSockaddr = (LPSOCKADDR) &blueInfo;
    sockInfo.RemoteAddr.iSockaddrLength = sizeof(SOCKADDR_BTH);
    sockInfo.RemoteAddr.lpSockaddr = (LPSOCKADDR) &blueInfo;

    WSAQUERYSET wsaq = {0};
    wsaq.lpszServiceInstanceName = (LPSTR) "BinaryReceptor";
    wsaq.lpszComment = (LPSTR) "Made to allow BinaryEye to send scans to a seperate device.";
    wsaq.lpServiceClassId = (LPGUID) &guid;
    wsaq.dwNameSpace = NS_BTH;
    wsaq.dwNumberOfCsAddrs = 1;
    wsaq.dwSize = sizeof(WSAQUERYSET);
    wsaq.lpcsaBuffer = &sockInfo;

    
    if (SOCKET_ERROR == WSASetService(&wsaq, RNRSERVICE_REGISTER, 0))
    {
        cout << "Error advertising service. Please try again.\n";
        cout <<WSAGetLastError();
        return;
    }

    if (SOCKET_ERROR == listen(blueSocket, 1))
    {
        cout << "Error listening on socket. Please try again.\n";
        cout << WSAGetLastError();
        return;
    }

    cout << "Waiting for connection...\n";
    KeyProcessor keyProc = KeyProcessor(settings);

    while(true)
    {

        SOCKADDR_BTH clientInfo;
        int clientInfoSize = sizeof(SOCKADDR_BTH) * 2;
        SOCKET client = accept(blueSocket, (struct sockaddr *) &clientInfo, &clientInfoSize);

        if (INVALID_SOCKET == client)
        {
            cout << "Error creating server-client socket. Please try again.\n";
            cout << WSAGetLastError();
            closesocket(client);
            return; 
        }

        string bluethoothDeviceName =  getBluetoothDeviceName(clientInfo.btAddr);
        if(bluethoothDeviceName == "")
        {
            cout << "Error getting connecting device's name.\n"; 
            cout << WSAGetLastError() << "\nConnected!";
        }
        else
        {
            cout << "Now connected to " << bluethoothDeviceName << ".\n";
        }

        int length = 1;

        while(true)
        {
            char* textBuffer = new char[1024];
            
            length = recv(client, textBuffer, 1024, 0);
            if (length <= 0) //occurs on disconnect of bluetooth client. needed for clean break instead of error.
                break;
            //bluetooth ends with \n. cut it off to allow user choice
            string text (textBuffer, length-1);

            cout << text << "\n";
            keyProc.typeText(text);
        }

        cout << "Disconnected.\n";
    }
}


string BluetoothConnector::getBluetoothDeviceName(int bluetoothAddress)
{
    HANDLE iter = {0};
    char buffer[1024];
    DWORD flags = LUP_CONTAINERS | LUP_RETURN_NAME | LUP_RES_SERVICE | LUP_RETURN_ADDR;
    LPWSAQUERYSET wsaqResult = (LPWSAQUERYSET)buffer;
    WSAQUERYSET clientWsaq = {0};
    clientWsaq.dwNameSpace = NS_BTH;
    clientWsaq.dwSize = sizeof(WSAQUERYSET);

    if (SOCKET_ERROR == WSALookupServiceBegin(&clientWsaq, flags, &iter))
    {
        return "";
    }
    
    wsaqResult->dwNameSpace = NS_BTH;
    wsaqResult->dwSize = sizeof(WSAQUERYSET);
    DWORD buffSize = sizeof(buffer);

    WSAPROTOCOL_INFO protocolInfo;
    int protocolInfoSize = sizeof(protocolInfo);
    SOCKET dummySocket = socket(AF_BTH, SOCK_STREAM, BTHPROTO_RFCOMM);
    getsockopt(dummySocket, SOL_SOCKET, SO_PROTOCOL_INFO, (char*)&protocolInfo, &protocolInfoSize);
    closesocket(dummySocket);

    while (SOCKET_ERROR != WSALookupServiceNext(iter, flags, &buffSize, wsaqResult))
    {
        char addressChar[50];
        DWORD addressSize = sizeof(addressChar);

        addressSize = sizeof(addressChar);
        WSAAddressToString(wsaqResult->lpcsaBuffer->RemoteAddr.lpSockaddr, wsaqResult->lpcsaBuffer->RemoteAddr.iSockaddrLength, &protocolInfo, addressChar, &addressSize);
       
        string addressStr = "(" + std::string(addressChar).substr(7,12);

        if (addressStr == intToBluetooth(bluetoothAddress))
        {
            return wsaqResult->lpszServiceInstanceName;
        }
    }

    return "";
}
