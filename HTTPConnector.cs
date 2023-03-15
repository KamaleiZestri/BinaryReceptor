using System.Diagnostics;
using System.Net;
using System.Runtime.InteropServices;
using System.Net.Sockets;
using System.Text.Json;

namespace BinaryReceptor
{
    public class HTTPConnector
    {
        private int universalPort;
        private const string pathToSettings = "wwwroot/ServerData.json";
        public HTTPConnector(int port)
        {
            universalPort = port;
        }
        public void startServer(Mode mode)
        {
            ServerData serverSettings;
            if(File.Exists(pathToSettings))
                serverSettings = JsonSerializer.Deserialize<ServerData>(File.ReadAllText(pathToSettings));
            else
            {
                serverSettings = new ServerData();
                serverSettings.IPAddress = "http://127.0.0.1";
            }
            var builder = WebApplication.CreateBuilder();

            serverSettings.mode = mode;
            
            builder.WebHost.UseKestrel(options => 
            {
                options.Listen(IPAddress.Loopback, universalPort);
                if(mode == Mode.HTTP)
                {
                    //TODO maybe change this to the specific one saved to settings? 
                    options.Listen(IPAddress.Any, universalPort);
                }
            });

            var app = builder.Build();
            app.UseDefaultFiles();
            app.UseStaticFiles();
  
            if(mode == Mode.HTTP)
            {
                KeyProcessor binrec = new KeyProcessor();

                app.MapGet("/recept/", async context => binrec.handleWebPage(context));
                serverSettings.IPAddress = getIPAddress(universalPort);
            }

            if(mode == Mode.BLUETOOTH)
            {
                Thread thr= new Thread(delegate()
                {
                    BluetoothConnector blue = new BluetoothConnector();
                    blue.startServer();
                });
                thr.Start();
            }

            File.WriteAllText(pathToSettings, JsonSerializer.Serialize(serverSettings));

            showWebpage("http://localhost:" + universalPort);
            app.Run();
        }
        private static string getIPAddress(int port)
        {
            var ipList = Dns.GetHostAddresses(Dns.GetHostName());
            
            //TODO Detect first IPv4 that isn't loopback. Can still fail however...
            foreach(IPAddress ip in ipList)
            {
                if(ip.AddressFamily == AddressFamily.InterNetwork && !IPAddress.IsLoopback(ip))
                {
                    return "http://" + ip.ToString() + ":" + port.ToString();
                }
            }
            return "http://0.0.0.0";
        }
        private static void showWebpage(string url)
        {
            try
            {
                Process.Start(url);
            }
            catch
            {
                // hack because of this: https://github.com/dotnet/corefx/issues/10361
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                {
                    url = url.Replace("&", "^&");
                    Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
                }
                else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                {
                    Process.Start("xdg-open", url);
                }
                else if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                {
                    Process.Start("open", url);
                }
                else
                {
                    throw;
                }
            }
        }
    }
}