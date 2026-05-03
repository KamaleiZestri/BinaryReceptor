# Binary Receptor
*Only for Windows, for now.*

Works with [BinaryEye](https://github.com/markusfisch/BinaryEye) to recieve scans and output them as keypresses. Utilizes either bluetooth or http.


## Usage

### On Computer
1. Navigate to the folder with BinaryReceptorGUI.exe.
2. Double click to run it with settings in `settings.ini` or open CMD for options.
3. Or use `BinaryReceptor.exe` for the cmd version. The following options exist:

```start BinaryReceptor.exe [bluetooth|http] [port]```
Parameters | Description
---|---
bluetooth | Default launch mode. Reccomended. Recieves BinaryEye scans via bluetooth.
http | Recieves BinaryEye scans via http. Not reccomended due to vulnerability of exposing keyboard input to http.
port | Optional. Changes the default port number from ```24234```

### On BinaryEye
1. `Settings` -> `Forwarding` section.
2. If Bluetooth:
    - Enable `Forward scans with Bluetooth`
    - Connect your device with BinaryEye to your device with BinaryReceptor via bluetooth.
    - Set `Host` to your your device with BinaryReceptor.

3. If HTTP: 
    - Enable `Forward Scans`.
    - Set `Request Type` to `GET and simply add content`
    - Add your current ip to `URL to forward to`


## Build Steps
1. Download requirements:
  - [Haxe](https://haxe.org)
  - [Dotnet compiler](https://dotnet.microsoft.com/en-us/download)
  - [Just](https://github.com/casey/just) (optional)

2. Download Haxe dependencies for this project with the following commands:
    - `haxelib install hxcpp 4.3.2` 
    - `haxelib git hxBluetooth https://github.com/KamaleiZestri/hxBluetooth`
    - `haxelib git hxKeyType https://github.com/KamaleiZestri/hxKeyType`

3. If using just, then run `just fullrelease`. Otherwise, read `justfile`. Its simple.
