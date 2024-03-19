#include <iostream>
#include <sstream>
#include <string>
#include <map>
#include "mode.hpp"

using namespace std;

string strToLower (string str)
{
    string result = "";

    for(int i=0; i< str.length(); i++)
    {
        result += tolower(str[i]);
    }

    return result;
}

string strToLower(char* psuedostr)
{
    return strToLower(string(psuedostr));
}

string parseSpecialInputs(string str, string delimiters)
{
    //TODO expand with more escapes. shift, cmd, alt, delete, space? updownleftright, home, pgup, pgdown, end
    map<string, string> escapes 
    {
        {"Enter", "\n"},
        {"Tab", "\t"},
        {"Backspace", "\b"}
    };
    string result = "";

    while(str.length()>0)
    {
        int begin;
        int end;

        if (delimiters.length() >=2)
        {
            begin = str.find(delimiters[0]);
            end = str.find(delimiters[1], begin+1);
        }
        else if (delimiters.length() == 1)
        {
            begin = str.find(delimiters[0]);
            end = str.find(delimiters[0], begin+1);
        }
        else    //do no parsing if no delimiters provided
            break;

        //if no escapes found, dump to result and exit
        if (begin == string::npos || end == string::npos)
        {
            result += str;
            break;
        }

        string potentialMatch = str.substr(begin+1, end-begin-1);
        auto iter = escapes.find(potentialMatch);

        //when valid escape, replace and dump all prior chars into result
        if (iter != escapes.end())
        {
            result += str.substr(0,begin);
            result += iter->second;
        }
        else
        {
            result += str.substr(0,end+1);
        }

        str = str.substr(end+1);
    }

    return result;
}

string intToBluetooth (int blueAddr)
{
    stringstream tempstream;
    string tempstr = "";
    string result ="(";

    tempstream << std::hex << blueAddr;
    tempstream >> tempstr;

    while(tempstr.length()>1)
    {
        result += toupper(tempstr[0]); 
        result += toupper(tempstr[1]);
        tempstr = tempstr.substr(2,tempstr.length()-2);

        if (tempstr.length()>1)
            result += ":";
    }
    
    result += ")";
    return result;
}
