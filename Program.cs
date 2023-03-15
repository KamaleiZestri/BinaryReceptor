using System.Diagnostics;
using System.Net;
using System.Runtime.InteropServices;
using System.Net.Sockets;
using System.Text.Json;

/// <summary>
/// The entry point.
/// </summary>
namespace BinaryReceptor
{
    public static class Program
    {
        public static void Main(string[] args)
        {
            int universalPort = 24234;
            HTTPConnector server = new HTTPConnector(universalPort);

            if (args.Length == 0)
                run(server, "bluetooth");
            else if (args.Length == 1)
                run(server, args[0]);
            else if(args.Length >= 2)
            {
                server = new HTTPConnector(int.Parse(args[1]));
                run(server, args[0]);
            }
            else
                Console.WriteLine("Error processing args. Try again.");
        }

        public static void run(HTTPConnector connect, string modeString)
        {
            Mode mode = Mode.BLUETOOTH;

            if(modeString.ToLower().Equals("http"))
            {
                mode = Mode.HTTP;
                Console.WriteLine("Starting HTTP mode...");
            }
            else if(modeString.ToLower().Equals("bluetooth"))
                Console.WriteLine("Starting Bluetooth mode...");
            else
            {
                Console.WriteLine("Error processing args. Try again.");
                return;
            }


            connect.startServer(mode);
        }
    }
}