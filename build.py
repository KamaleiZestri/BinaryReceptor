import subprocess
import sys


def buildDebugWindowsCmd():
    subprocess.run([
        "dotnet", "build", 
        "BinaryReceptor.Cmd/BinaryReceptor.Cmd.csproj", 
        "--framework:net472"
    ])

def buildDebugWindowsGui():
    subprocess.run([
        "dotnet", "build", 
        "BinaryReceptor.Cmd/BinaryReceptor.Cmd.csproj", 
        "--framework:net472",
        "--output:BinaryReceptor.WinGui/bin/Debug/net472/win-x64/"
    ])
    subprocess.run([
        "dotnet", "build",
        "BinaryReceptor.WinGui.csproj", 
        "--framework:net472"
    ])

def buildWindowsRelease():
    subprocess.run([
        "dotnet", "publish"
        "BinaryReceptor.Cmd/BinaryReceptor.Cmd.csproj",
        "--framework:net472",
        "--output:release"
    ])
    subprocess.run([
        "dotnet", "publish",
        "BinaryReceptor.WinGui/BinaryReceptor.WinGui.csproj", 
        "--framework:net472",
        "--output:release"
    ])


# release = "dotnet publish --framework:net472"

# for gui 
# <!-- BUILD COMMAND -->
# <!-- dotnet publish -f net462 -->

match sys.argv[1]:
    case "debug-windows-cmd":
        buildDebugWindowsCmd()
    case "debug-windows-gui":
        buildDebugWindowsGui()
    case "release-windows":
        buildWindowsRelease()
    case "debug-linux-cmd":
        buildDebugLinuxCmd()
    case "release-linux":
        buildLinuxRelease()
    case _:
        print("Error. Invalid build argument.")
