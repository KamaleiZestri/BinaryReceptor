#include <iostream>
#include <regex>

#include <winsock2.h>

#pragma comment(lib, "Ws2_32.lib")

#include "http.hpp"
#include "keypress.hpp"

using namespace std;

HttpConnector::HttpConnector(ServerSettings& settings): settings(settings)
{
    WSADATA wsd;
    if (WSAStartup(MAKEWORD(2, 2), &wsd) != 0)
    {
        cout << "Unable to load WinSock version 2.2!";
    }
}

void HttpConnector::startServer()
{
    char* localIP = inet_ntoa (*(struct in_addr *)*gethostbyname("")->h_addr_list);
    SOCKET httpSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    if (INVALID_SOCKET == httpSocket)
    {
        cout << "Socket is invalid. Please try again.\n";
        cout << WSAGetLastError();
        return;
    }

    SOCKADDR_IN httpInfo = {0};
    httpInfo.sin_family = AF_INET;
    httpInfo.sin_addr.s_addr = inet_addr(localIP);
    httpInfo.sin_port = htons(settings.port);

    if (SOCKET_ERROR == bind(httpSocket, (struct sockaddr *) &httpInfo, sizeof(SOCKADDR_IN)))
    {
        cout << "Error binding socket. Please try again.\n";
        cout << WSAGetLastError();
        return;
    }

    if (SOCKET_ERROR == listen(httpSocket, 1))
    {
        cout << "Error listening on socket. Please try again.\n";
        cout << WSAGetLastError();
        return;
    }

    cout << "Waiting for connection at IP: " << localIP << ":" << settings.port << " ...\n";
    KeyProcessor keyProc = KeyProcessor(settings);

    while (true)
    {
        SOCKET client = accept(httpSocket, NULL, NULL);

        if (client == INVALID_SOCKET)
        {
            cout << "Error creating server-client socket. Please try again.\n";
            cout << WSAGetLastError();
            closesocket(client);
            return; 
        }

        cout << "Connected!\n";

        int length = 1;

        while(length > 0)
        {
            char* textBuffer = new char[1024];
            
            length = recv(client, textBuffer, 1024, 0);
            if (length <= 0) //occurs on disconnect of bluetooth client. needed for clean break instead of error.
                break;
            string text (textBuffer, length);
    
            //get the actual scan from the HTTP GET request
            int p1 = text.find("content=")+8;
            int p2 = text.find("&");
            string typeableText = text.substr(p1, p2 - p1);


            if(text.substr(length-2)=="\r\n")
                length = 0;

            //TODO send real http response
            send(client, "HTTP/1.1 200 OK\r\n", 18,0);
            
            cout << typeableText << "\n";
            keyProc.typeText(typeableText);
        }

        closesocket(client);
        cout << "Disconnected.\n";
    }
}
