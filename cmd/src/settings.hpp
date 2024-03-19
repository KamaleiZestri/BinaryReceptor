#ifndef __SERVERSETTINGS_HPP__
#define __SERVERSETTINGS_HPP__

#include <string>
#include <map>

#include "mode.hpp"

class ServerSettings
{
    private:
        std::map<std::string, std::string> loadArgs(int argc, char *argv[]);
        std::map<std::string, std::string> loadFile();
        bool loadSettings(std::map<std::string, std::string> settingsMap);

    public:
        Mode mode;
        std::string preType;
        std::string postType;
        int port;
        std::string delimiters;

        std::string settingsFileLoc;

        ServerSettings(int argc, char *argv[]);
        void saveSettingsToFile(std::map<std::string, std::string> argsMap);

};

#endif
