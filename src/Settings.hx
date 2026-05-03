package;

import Mode;
import StringTools;
import sys.FileSystem;
import sys.io.File;

class Settings
{
    public var settingsFileLoc:String;
    public var mode:Mode;
    public var preType:String;
    public var postType:String;
    public var port:Int;
    public var delimiters:String;

    public static final instance:Settings = new Settings();

    private function new() {}

    public function loadSettings()
    {
        //TODO delete var settingsFileLoc = '${Sys.getCwd()}settings.ini';   
        var settingsFileLoc = "settings.ini";
        var loaded = ["" => ""];

        if(!FileSystem.exists(settingsFileLoc))
            Sys.println("Settings file does not exists. Using defaults...");
        else
            loaded = readIniFile(settingsFileLoc);

        // Assign settings from map 
        for(variable in Type.getInstanceFields(Settings))
        {
            if(loaded.exists(variable.toLowerCase()))
                Reflect.setField(this, variable, loaded[variable.toLowerCase()]);
        }

        /******** Assign all settings defaults *********/ 
        if (!loaded.exists("mode"))
            mode = Mode.BLUETOOTH; //TODO handle mode
        if (!loaded.exists("preType"))
            preType = "";
        if (!loaded.exists("postyType"))
            postType = "\n";
        if (!loaded.exists("port"))
            port = 24234;
        if (!loaded.exists("delimiters"))
            delimiters = "{}";
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

    /**
        Reads simple .ini formatted file. Returns key:value map. 
    **/
    private function readIniFile(settingsFileLoc:String):Map<String,String>
    {
        var sett = ["" => ""];
        var rawSett = File.getContent(settingsFileLoc);

        for (line in rawSett.split("\n"))
        {
            if (line.charAt(0) == ";")
                continue;
            
            if (!StringTools.contains(line,"="))
                continue;

            var equalsLoc = line.indexOf("=");
            var key = line.substring(0,equalsLoc);
            var value = line.substring(equalsLoc + 1, line.length);

            sett[ StringTools.trim(key)] =  StringTools.trim(value);    
        }

        return sett;
    }
}
