using InTheHand.Net.Sockets;
using InTheHand.Net.Bluetooth;

namespace BinaryReceptor
{
    public class BluetoothConnector
    {
        static private string remnumuuid = "6be5ccef-5d32-48e3-a3a0-d89e558a40f1";
        static private string uuid = "8a8478c9-2ca8-404b-a0de-101f34ab71ae";
        static BluetoothListener listener = new BluetoothListener(new Guid(uuid));
        private KeyProcessor binrec = new KeyProcessor();

        public void startServer()
        {
            listener.Start();
            Console.WriteLine("Waiting for connection...");

            while(true)
            {
                var client = listener.AcceptBluetoothClient();
                Console.WriteLine(client.RemoteMachineName);
                var stream = client.GetStream();
                StreamReader sr = new StreamReader(stream, System.Text.Encoding.UTF8);

                //client.connected doesnt work. https://github.com/inthehand/32feet/issues/252
                try
                {
                    while(true)
                    {
                        string text = sr.ReadLine();
                        if (text == null)
                            break;
                        Console.WriteLine(text);
                        binrec.typeText(text);
                    }
                }
                catch(Exception)
                {
                    Console.WriteLine("Disconnected");
                    client.Close();
                    break;
                }
            }
        }
    }
}