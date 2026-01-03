package;

import Mode;
import ServerSettings;
import hxBluetooth.BthAddr;
import hxBluetooth.UUID;
import hxKeyType.KeyProcessor;

class Main 
{
    public static function main ():Void 
    {
        // TODO args like {Enter} and {Tab} need handling
        // ServerSettings.instance.loadSettings();
        ServerSettings.instance.loadArgs(Sys.args());
        
        if (ServerSettings.instance.mode == Mode.BLUETOOTH)
            startBluetooth();
        else 
            startHttp();        
    }


    public static function startHttp():Void
    {
        Sys.println("HTTP not implemented...");
        // TODO http stub...
        // var http = HttpConnector(settings);
        // http.startServer();
    }

    public static function startBluetooth()
    {
        var guid = new UUID("8a8478c9-2ca8-404b-a0de-101f34ab71ae");
        var name = "BinaryRecetor";
        var comment = "Made to allow BinaryEye to send scans to a seperate device.";

        var blueServer = new BluetoothSocket();

        blueServer.bind(guid,name,comment);
        blueServer.listen();
        Sys.println("Waiting for connection...");
        
        while(true)
        {
            var client = blueServer.accept();
            Sys.println('Now connected to ${client.peer()}');

            while (true)
            {
                try 
                {
                    var content = client.read();
                    if (content == "")
                        break;
                    else
                    {
                        Sys.print(content);
                        KeyProcessor.typeString(content);
                    }
                }
                catch(e:Dynamic)
                {
                    trace(e);
                    break;
                }
            }
            client.close();
            Sys.println("Disconnected...");
        }
        blueServer.close();
    }
}
