# Binary Receptor
*Only for Windows, due to C# Bluetooth API limitations.*

Works with [BinaryEye](https://github.com/markusfisch/BinaryEye) to recieve scans and output them as keypresses. Utilizes either bluetooth or http.

For a windows tray version, see [here](https://github.com/KamaleiZestri/BinaryReceptorWindows)

## Usage
1. Navigate to the folder with BinaryReceptor.exe.
2. Double click to run it with defaults or open CMD for options.
3. In CMD, use:

```start BinaryReceptor.exe [bluetooth|http] [port]```
Parameters | Description
---|---
bluetooth | Default launch mode. Reccomended. Recieves BinaryEye scans via bluetooth.
http | Recieves BinaryEye scans via http. Not reccomended due to vulnerability of exposing keyboard input to http.
port | Optional. Changes the default port number from ```24234```
