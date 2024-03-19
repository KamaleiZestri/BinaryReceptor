#ifndef __KEYPROCESSOR_HPP__
#define __KEYPROCESSOR_HPP__

#include <cstddef>
#include <string>
#include "settings.hpp"

using namespace std;

class KeyProcessor
{
    public:
        KeyProcessor(ServerSettings& settings);
        void typeText(string text);
    private:
        ServerSettings &settings;
        INPUT keyInput(char VkKey, int flags);
        INPUT shiftStateInput(int effect, int flags);
        BYTE shiftStateInput(int effect);
};

#endif
