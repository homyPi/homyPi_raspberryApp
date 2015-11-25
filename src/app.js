var ini = require('node-ini');

var socketConnection = require("./node/socketConnection");
var serverConnection = require("./node/serverConnection");
var modulesManager = require("./node/modulesManager");
var serverRequest = require("./node/serverRequest");

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
var app = {
    settings: {
        host: config.Server.url,
        username: config.Server.username,
        password: config.Server.password
    },
    args: args,
    middleware: {}
};
socketConnection(app);
serverConnection(app);
modulesManager(app);


function connect() {
    "use strict";
    console.log("Starting...");
    var raspInfo = {
        name: "Jonny",
        ip : "92.68.1.0",
        modules: {}
    }
    app.middleware.socketConnection.connect(raspInfo,
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
var stop = function(err, status){
	console.log({error: err, status: status});
	process.stdin.resume();
	app.middleware.modulesManager.killAll();
	process.exit(2);
};

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


module.exports = app;

