package;

import Mode;
import Settings;
import hxbluetooth.BluetoothSocket;
import hxbluetooth.UUID;
import hxkeytype.KeyProcessor;
import sys.net.Host;
import sys.net.Socket;

class Main 
{
    public static function main ():Void 
    {
        // TODO args like {Enter} and {Tab} need handling?
        Settings.instance.loadSettings();
        Settings.instance.loadArgs(Sys.args());
        
        if (Settings.instance.mode == Mode.BLUETOOTH)
            startBluetooth();
        else 
            startHttp();        
    }


    public static function startHttp():Void
    {
        Sys.println("HTTP not implemented...");
        var host = new Host(Host.localhost());
        var serverIp = '${host.host}:${Settings.instance.port}';
        var httpServer = new Socket();

        Sys.println("Starting HTTP server.");

        httpServer.bind(host, Settings.instance.port);
        httpServer.listen(1);
        Sys.println('Waiting for connection at $serverIp...');
        
        while(true)
        {
            var client = httpServer.accept();
            Sys.print('Message received from ${client.peer()}: ');

            try 
            {
                var data = client.input.readLine();
                var content = parseGet(data);
                Sys.println(content);
                KeyProcessor.typeString(content);
                client.write("HTTP/1.1 200 OK\nConnection:Closed\r\n\n");
            }
            catch(e:Dynamic)
            {
                trace(e);
                client.write("HTTP/1.1 500 Server Error\nConnection:Closed\r\n\n");
                client.close();
                break;
            }
            client.close();
        }           
        httpServer.close();
    }

    private static function parseGet(header:String):String
    {
        var reg = ~/\?content=(\S+)/;
        var res = reg.match(header);

        if (!res)
            return "";

        return reg.matched(1);
    }

    public static function startBluetooth()
    {
        var guid = new UUID("8a8478c9-2ca8-404b-a0de-101f34ab71ae");
        var name = "BinaryRecetor";
        var comment = "Made to allow BinaryEye to send scans to a seperate device.";

        var blueServer = new BluetoothSocket();

        Sys.println("Starting Bluetooth server.");

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
                        Sys.println(content);
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
