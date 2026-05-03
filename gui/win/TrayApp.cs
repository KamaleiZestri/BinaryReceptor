using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

using System.Windows.Forms;

using System.ComponentModel;
using System.Diagnostics;
using System.Reflection;
using System.Configuration;

namespace BinRecTray;

public class TrayApp : ApplicationContext
{
    private const string TrayIconResource = "BinaryReceptorGUI.icon.ico";
    private string ProgName;
    private string mode = "bluetooth";
    private NotifyIcon trayIcon;
    private ToolStripMenuItem menuItemMode;
    private ToolStripMenuItem menuItemSwitch;
    private ToolStripMenuItem menuItemStart;
    private ToolStripMenuItem menuItemStop;
    private ToolStripMenuItem menuItemExit;
    
    public TrayApp(string progname)
    {
        this.ProgName = progname;
        CreateTrayIcon();
        Start(null,null);
    }

    private void CreateTrayIcon()
    {
        menuItemMode = new ToolStripMenuItem("Mode: Bluetooth", null, Switch);
        menuItemSwitch = new ToolStripMenuItem("Switch Modes", null, Switch);
        menuItemStart = new ToolStripMenuItem("Start", null, Start);
        menuItemStop = new ToolStripMenuItem("Stop", null, Stop);
        menuItemExit = new ToolStripMenuItem("Exit", null, Exit);

        ContextMenuStrip contextMenu = new ContextMenuStrip();
        contextMenu.Items.Add(menuItemMode);
        contextMenu.Items.Add(menuItemSwitch);
        contextMenu.Items.Add(new ToolStripSeparator());
        contextMenu.Items.Add(menuItemStart);
        contextMenu.Items.Add(menuItemStop);
        contextMenu.Items.Add(menuItemExit);

        contextMenu.Opening += new CancelEventHandler(ContextMenuOnPopup);
        
        using var iconStream = Assembly.GetExecutingAssembly().GetManifestResourceStream(TrayIconResource);
        trayIcon = new NotifyIcon() 
        {
            Icon = new Icon(iconStream), 
            ContextMenuStrip = contextMenu, 
            Visible = true, 
            Text = ProgName
        };
    }
    private void Switch(object sender, EventArgs e)
    {
        Stop(null, null);
        if (mode == "bluetooth")
            mode = "http";
        else
            mode = "bluetooth";
    }
    private void Start(object sender, EventArgs e)
    {
        string modeString = "--mode bluetooth";
        if (mode == "http")
            modeString = "--mode http";

        Process p = new Process();
        p.StartInfo.FileName = String.Concat(ProgName,".exe");
        p.StartInfo.CreateNoWindow = true;
        p.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
        p.StartInfo.WorkingDirectory = Application.StartupPath;
        p.StartInfo.Arguments = modeString;
        p.Start();
    }
    private void Stop(object sender, EventArgs e)
    {
        Process? process = Process.GetProcessesByName(ProgName).FirstOrDefault();
        if (process == null)
            return;

        if (!process.CloseMainWindow())
            process.Kill();
    }
    private void Exit(object sender, EventArgs e)
    {
        Stop(null, null);
        trayIcon.Visible = false;
        Application.Exit();
    }
    private void ContextMenuOnPopup(object sender, EventArgs e)
    {
        bool exeRunning = Process.GetProcessesByName(ProgName).Length > 0;
        bool running = exeRunning;
        bool stopped = !exeRunning;

        menuItemStart.Enabled = stopped;
        menuItemStop.Enabled = running;

        if (mode == "bluetooth")
            menuItemMode.Text = "Mode: Bluetooth";
        else
            menuItemMode.Text = "Mode: HTTP";
    } 
}
