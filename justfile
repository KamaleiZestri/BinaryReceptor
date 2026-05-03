set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
PACKAGEDIR := "build\\BinaryReceptor"

[private]
default:
  @just --list

#Install haxe dependencies
haxedeps:
    haxelib install hxcpp 4.3.2 
    haxelib git hxBluetooth https://github.com/KamaleiZestri/hxBluetooth
    haxelib git hxKeyType https://github.com/KamaleiZestri/hxKeyType

# Build and package to deliver 
fullrelease:
  just buildTray
  just buildRelease
  just packageRelease

buildTray:
  dotnet publish gui\win 

# Build normal release version
buildRelease:
  haxe release.hxml

# Package built tray,app, and anything else needed for FULL release
packageRelease:
  mkdir "{{PACKAGEDIR}}" -f
  cp "build\\release\\BinaryReceptor.exe" "{{PACKAGEDIR}}\\BinaryReceptor.exe"
  cp "gui\\win\\bin\\Release\\net8.0-windows\\win-x64\\publish\\BinaryReceptorGUI.exe" "{{PACKAGEDIR}}\\BinaryReceptorGUI.exe"
  cp "res\\default-settings.ini" "{{PACKAGEDIR}}\\settings.ini"
  Compress-Archive -Force "{{PACKAGEDIR}}" "BinaryReceptor.zip"

# Clean build and temp files.
clean:
  rm -r -fo "BinaryReceptor.zip"
  rm -r -fo "build"
  rm -r -fo "gui\\win\\obj"
  rm -r -fo "gui\\win\\bin"
