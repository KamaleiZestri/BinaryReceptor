#include <windows.h>
#include <winuser.h>

#include <cstddef>
#include <string>
#include <vector>
#include <ctype.h>
#include "util.hpp"
#include "keypress.hpp"

using namespace std;

KeyProcessor::KeyProcessor(ServerSettings& settings): settings(settings){}

INPUT KeyProcessor::keyInput(char VkKey, int flags)
{
    INPUT ip;
    ip.type = INPUT_KEYBOARD;  

    ip.ki.wVk = VkKey;
    ip.ki.dwFlags = flags;
    
    return ip;
}

INPUT KeyProcessor::shiftStateInput(int effect, int flags)
{
    INPUT ip;
    ip.type = INPUT_KEYBOARD;

    ip.ki.dwFlags = flags;

    switch (effect)
    {
    case 1: //shift
        ip.ki.wVk = VK_SHIFT;
        break;
    case 2: //CTRL
        ip.ki.wVk = VK_CONTROL;
        break;
    case 4: //ALT
         ip.ki.wVk = VK_MENU;
        break;
    // case 8: //Hankaku
    //      ip.ki.wVk =
    default:
        break;
    }

    return ip;
}

// void KeyProcessor::typeText(string text)
// {
//     vector<INPUT> keyPresses;

//     text = settings.preType + text + settings.postType;

//     for (int i=0; i<text.length(); i++)
//     {
//         char chara = text[i];
//         short keyScan = VkKeyScan(chara);
//         char keyCode = keyScan;
//         //refer to https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-vkkeyscanexa
//         int effect = keyScan>>8;
        
//         if (effect != 0)
//             keyPresses.push_back(shiftStateInput(effect, 0));

//         keyPresses.push_back(keyInput(keyCode, 0));
//         keyPresses.push_back(keyInput(keyCode, KEYEVENTF_KEYUP));

//         if (effect != 0)
//             keyPresses.push_back(shiftStateInput(effect, KEYEVENTF_KEYUP));
//     }

    
//     SendInput(keyPresses.size(), keyPresses.data(), sizeof(INPUT));
// }

BYTE KeyProcessor::shiftStateInput(int effect)
{
    BYTE keyCode;

    switch (effect)
    {
    case 1: //shift
        keyCode = VK_SHIFT;
        break;
    case 2: //CTRL
        keyCode = VK_CONTROL;
        break;
    case 4: //ALT
        keyCode = VK_MENU;
        break;
    // case 8: //Hankaku
    //      keyCode =
    default:
        break;
    }

    return keyCode;
}

// keybdevent is used instead of SendInput due to the way certain keys (like Enter) or processed.
// If using SendInput, then the keypress is often output as text whether than pressed like an actual key.
//TODO maybe add SendInput as an option
void KeyProcessor::typeText(string text)
{
    vector<INPUT> keyPresses;

    text = settings.preType + text + settings.postType;

    for (int i=0; i<text.length(); i++)
    {
        char chara = text[i];
        short keyScan = VkKeyScan(chara);
        char keyCode = keyScan;
        //refer to https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-vkkeyscanexa
        int effect = keyScan>>8;


        //if "Enter" is attempted to be pressed when checking for modifier keys, it prints oddly.
        //for example, in Notepad++ it just doesn't skip to the next line.
        //in Google Sheets it goes to the next line in the same cell and does not go to the next cell
        //this may also occur with other special keys.
        if (keyCode < 0x30) 
        {
            keybd_event(keyCode, 0, 0, 0);
            continue;
        }


        if (effect != 0)
            keybd_event(shiftStateInput(effect), 0, 0, 0);

        keybd_event(keyCode, 0, 0, 0);

        if (effect != 0)
            keybd_event(shiftStateInput(effect), 0, KEYEVENTF_KEYUP, 0);

        keybd_event(keyCode, 0, KEYEVENTF_KEYUP, 0);    

        Sleep(1);
    }

}