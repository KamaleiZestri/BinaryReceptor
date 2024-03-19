#include <string>
#include <map>
#include <iostream>
#include <fstream>

#include "mode.hpp"
#include "util.hpp"
#include "settings.hpp"

using namespace std;

ServerSettings::ServerSettings(int argc, char *argv[])
{

    #ifdef WINDOWS
        settingsFileLoc = "settings.ini";
    #endif
    //TODO linux. location in xdg-dotconfig/BinaryReceptor/settings.ini
    
    mode = Mode::BLUETOOTH;
    preType = "";
    postType = "\n";
    port = 24234;
    delimiters = "{}";

    map<string, string> fileMap = loadFile();
    map<string, string> argsMap = loadArgs(argc, argv);
    bool fileExists = loadSettings(fileMap);
    loadSettings(argsMap);

    if(!fileExists)
        saveSettingsToFile(argsMap);

}

map<string, string> ServerSettings::loadArgs(int argc, char *argv[])
{
    map<string, string> argsMap;
    string validArgs[] = {"--mode", "--preType", "--postType", "--port", "--delimiters"};

    for(int i=0; i+1 < argc; i++)
    {
        string arg = argv[i];
        string val = argv[i+1];

        for(int k=0;k<sizeof(validArgs)/sizeof(validArgs[0]);k++)
        {
            if (arg == validArgs[k])
            {
                argsMap[arg.substr(2, arg.length())] = val;
                break;
            }  
        }
    }
    return argsMap; 
}

map<string, string> ServerSettings::loadFile()
{
    map<string, string> fileMap;
    string line;
    string key;
    string value;
    ifstream settingsFile;
    settingsFile.open(settingsFileLoc);

    while (getline(settingsFile,line))
    {
        if (line[0] == ';')
            continue;
        
        if (!line.find("="))
            continue;

        value = line.substr(line.find('=')+1);
        key = line.substr(0, line.find('='));
        fileMap[key] = value;
    }

    settingsFile.close();
    return fileMap;
}

bool ServerSettings::loadSettings(map<string, string> settingsMap)
{
    bool anySettings = false;
    if (settingsMap.count("mode") > 0)
    {
        if (strToLower(settingsMap["mode"]) == "bluetooth")
            mode = Mode::BLUETOOTH;
        if (strToLower(settingsMap["mode"]) == "http")
            mode = Mode::HTTP;

        anySettings = true;
    }

    if (settingsMap.count("delimiters") > 0)
    {
        delimiters = settingsMap["delimiters"];
        anySettings = true;
    }

    if (settingsMap.count("preType") > 0)
    {
        preType = parseSpecialInputs(settingsMap["preType"], delimiters);
        anySettings = true;
    }

    if (settingsMap.count("postType") > 0)
    {
        postType = parseSpecialInputs(settingsMap["postType"], delimiters);
        anySettings = true;
    }

    if (settingsMap.count("port") > 0)
    {
        port = stoi(settingsMap["port"]);
        anySettings = true;
    }

    return anySettings;
}

void ServerSettings::saveSettingsToFile(map<string, string> settingsMap)
{
    ofstream settingsFile;
    settingsFile.open(settingsFileLoc);

    if (settingsMap.count("mode") > 0)
    {
        if (mode == Mode::BLUETOOTH)
            settingsFile << "mode=bluetooth\n";
        else
           settingsFile << "mode=http\n";
    }
    else
        settingsFile << "mode=bluetooth\n";

    if (settingsMap.count("preType") > 0)
        settingsFile << "preType=" << settingsMap["preType"] << "\n";
    else
        settingsFile << "preType=\n";

    if (settingsMap.count("postType") > 0)
        settingsFile << "postType=" << settingsMap["postType"] << "\n";
    else
        settingsFile << "postType={Enter}\n";

    if (settingsMap.count("port") > 0)
        settingsFile << "port=" << settingsMap["port"] << "\n";
    else
        settingsFile << "port=24234\n";

    if (settingsMap.count("delimiters") > 0)
        settingsFile << "delimiters=" << settingsMap["delimiters"] << "\n";
    else
        settingsFile << "delimiters={}\n";

    settingsFile.close();
}
