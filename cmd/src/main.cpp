#include <iostream>
#include "util.hpp"
#include "settings.hpp"
#include "starter.hpp"

using namespace std;

int main(int argc, char *argv[])
{
    ServerSettings settings = ServerSettings(argc, argv);
    ConnectorStarter starter = ConnectorStarter(settings);

    starter.startConnector();
    
    return 0;
}
