package;

import Mode;
import StringTools;
import sys.FileSystem;
import sys.io.File;

class ServerSettings
{
    public var settingsFileLoc:String;
    public var mode:Mode;
    public var preType:String;
    public var postType:String;
    public var port:Int;
    public var delimiters:String;

    public static final instance:ServerSettings = new ServerSettings();

    private function new()
    {
        mode = Mode.BLUETOOTH;
        preType = "";
        postType = "\n";
        port = 24234;
        delimiters = "{}";

        settingsFileLoc = '${Sys.getCwd()}settings.ini';
    }

    public function loadArgs(args:Array<String>)
    {
        var i = 0;
        while (i < args.length)
        {
            switch args[i]
            {
                case "--mode":
                    if (args[i+1].toLowerCase() == "bluetooth")
                        mode = Mode.BLUETOOTH;
                    else if (args[i+1].toLowerCase() == "http")
                        mode = Mode.HTTP;
                    else
                        throw('Invalid mode: ${args[i+1]}');
                    i+=2;
                case "--postType":
                    postType = args[i+1];
                    i+=2;
                case "--preType":
                    preType = args[i+1];
                    i+=2;
                case "--delimiters":
                    delimiters = args[i+1];
                    i+=2;
                case "--port":
                    port = Std.parseInt(args[i+1]);
                    i+=2;
                default: i+=1;
            }
        }
    }

    public function loadSettings()
    {
        if (!FileSystem.exists(settingsFileLoc))
            return;

        var settingsFileContent = File.getContent(settingsFileLoc);

        for (line in settingsFileContent.split("\n"))
        {
            if (line.charAt(0) == ';')
                continue;
            
            if (!StringTools.contains(line, "="))
                continue;

            var equalsLoc = line.indexOf("=");

            var key = line.substring(0,equalsLoc);
            var value = StringTools.rtrim(line.substring(equalsLoc + 1, line.length));
            switch (key)
            {
                case "mode":
                    if (value.toLowerCase() == "bluetooth")
                        mode = Mode.BLUETOOTH;
                    else if (value.toLowerCase() == "http")
                        mode = Mode.HTTP;
                    else
                        throw('Invalid mode: ${value}');
                case "postType":
                    postType = value;
                case "preType":
                    preType = value;
                case "delimiters":
                    delimiters = value;
                case "port":
                    port = Std.parseInt(value);
                default: 
            }
        }
    }

    public function saveSettings()
    {  
        var fileout = File.write(settingsFileLoc);

        var settings = 'mode=${mode}\n' +
            'preType=${preType}\n' + 
            'postType=${postType}\n' + 
            'port=${port}\n'+
            'delimiters=${delimiters}';

        fileout.writeString(settings);
        fileout.close();
    }
}
