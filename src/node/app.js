var ini = require('node-ini');

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

var args = parser.parseArgs();

var confPath = args.conf || ((process.env.HOME || process.env.HOMEPATH || process.env.USERPROFILE) + '/.hapi_conf');
var config = ini.parseSync(confPath);
var app = {
    settings: {
        host: config.Server.url,
        username: config.Server.username,
        password: config.Server.password
    },
    args: args,
    middleware: {}
};
require("./socketConnection")(app);
require("./serverConnection")(app);
require("./modulesManager")(app);


function connect() {
    "use strict";
    console.log("Starting...");
    app.middleware.socketConnection.connect(function() {
        console.log("callback");
        require("./serverRequest")(app);
        //app.middleware.modulesManager.setSockets();
        //app.middleware.modulesManager.onConnected();
    });
}


process.on('exit', function() {
    process.stdin.resume();
    app.middleware.modulesManager.killAll();
    process.exit(2);
});
process.on('SIGINT', function() {
    process.stdin.resume();
    app.middleware.modulesManager.killAll();
    process.exit(2);
});

app.middleware.modulesManager.setupModules(app);
app.middleware.modulesManager.runModules(app)
    connect();


module.exports = app;

