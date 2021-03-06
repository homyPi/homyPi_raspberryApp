var ini = require('node-ini');
var socketConnection = require("./node/socketConnection");
var serverConnection = require("./node/serverConnection");
var modulesManager = require("./node/modulesManager");
var serverRequest = require("./node/serverRequest");
var utils = require("./node/utils");

var ArgumentParser = require('argparse').ArgumentParser;
var parser = new ArgumentParser({
    version : '0.0.1',
    addHelp : true,
    description : ''
});
parser.addArgument(['-c', '--conf'], {
    help : 'configuration file path'
});
parser.addArgument(['-a', '--alone'], {
    help : "don't run python scripts",
    action: "storeTrue"
});
parser.addArgument(['-m', '--modules'], {
    help : "names of the modules to launch (comma separated)"
});

var args = parser.parseArgs();

var confPath = args.conf || ((process.env.HOME || process.env.HOMEPATH || process.env.USERPROFILE) + '/.hommyPi_conf');
if (args.modules) {
	args.modules.replace(/ /g, "").split(",");
}
var config = ini.parseSync(confPath);
if (!config || !config.Server) {
	console.log("Missing server config");
	process.exit(2);
}
if (!config.Server.url || !config.Server.username || !config.Server.password) {
	console.log("invalid config file");
	process.exit(2);
}
var app = {};

function run() {
    app = {
        settings: {
            host: config.Server.url,
            username: config.Server.username,
            password: config.Server.password,
            name: config.Server.name
        },
        args: args,
        middleware: {}
    };
    socketConnection(app);
    serverConnection(app);
    modulesManager(app);
    checkConfig(config);


    function connect() {
        "use strict";
        console.log("Starting...");
        var raspInfo = {
            name: app.settings.name,
            ip : utils.getIpAddr()["wlan0"],
            modules: {}
        }
        app.middleware.socketConnection.connect(raspInfo, config.Server.url,
            function(token, reconnection) {
                console.log("callback");
                if (!reconnection) {
                    serverRequest(app);
                    app.middleware.modulesManager.setSockets();
                    app.middleware.modulesManager.runModules();
                } else {
                    try {
                    app.middleware.modulesManager.socketReconnected();
                }catch(e) {console.log(e);}
                }
            });
    }
    function stop(err, status){
        console.log({error: err, status: status});
        process.stdin.resume();
        app.middleware.modulesManager.killAll();
        process.exit(2);
    };
    function checkConfig(config) {
        if (!config) {
            stop("Missing configs", "exit");
            return;
        }
        if (!config.Server) {
            stop("Missing serveur configs", "exit");
            return;
        }
        if (!config.Server.username) {
            stop("Missing field username in configs", "exit");
            return;
        }
        if (!config.Server.password) {
            stop("Missing field password in configs", "exit");
            return;
        }
        if (!config.Server.name) {
            stop("Missing field name in configs", "exit");
            return;
        }
        if (!config.Server) {
            stop("Missing field in configs", "exit");
            return;
        }
    }

    process.on('exit', function() {
        stop(null, "exit");
    });
    process.on('SIGINT', function() {
        stop(null, "SIGINT");
    });
    var err = app.middleware.modulesManager.setupModules(app);
    if (err) {
        console.log(err);
        stop(err);
    }

    connect();
}




var pidlock = require('pidlock');
pidlock.guard('/tmp', 'homyPi_RaspberryApp', function(error, data, cleanup) {
  if (!error) {
    run();
  } else {
    console.log("Already running")
    process.exit(-1);
  }
});




module.exports = app;

