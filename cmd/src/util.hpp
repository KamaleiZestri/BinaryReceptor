#ifndef __UTIL_HPP__
#define __UTIL_HPP__


#include <string>
#include "mode.hpp"

using namespace std;

string strToLower(char* psuedostr);
string strToLower(string str);
string parseSpecialInputs(string str, string delimiters);
string intToBluetooth (int blueAddr);

#endif
