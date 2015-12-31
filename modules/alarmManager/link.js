
var route = "module.alarm";
var ps = require("ps-node");

var Link = function() {};
Link.app = null;
Link.sub = null;
Link.pub = null;
Link.started = false;
Link.context = require('rabbit.js').createContext();
Link.context.on('ready', function() {
    "use strict";
    Link.pub = Link.context.socket('PUBLISH', {routing: "direct"}), Link.sub = Link.context.socket('SUBSCRIBE', {routing: "direct"});
    Link.sub.connect(route+".link", route+".link", function() {
        Link.pub.connect(route, function() {
            console.log(route + " ready");
            Link.sub.on('data', function(message) {
                var json = JSON.parse(message);
                console.log("got " + JSON.stringify(json));
                if (json.message === "ready") {
                    Link.pub.write(JSON.stringify({
                        message : "ok"
                    }));
                }

            });
        });
    });
});

Link.killExisting = function(callback) {
    ps.lookup({
        command: "homyPi_alarmManager", psargs: 'ux'
    }, function(err, res) {
        if (err) {
            console.log("err: " + err);
            return callback(err);
        } else {
            var counter = 0;
            if (!res.length) {
                return callback();
            }
            for (var i = 0; i < res.length; i++) {
                counter++;
                //kill res[i].pid
                console.log("killing process " + res[i].pid);
                ps.kill(res[i].pid , function( err ) {
                    counter--;
                    if (counter === 0) {
                        return callback(err);
                    }
                });
            }
        }
    });
};

Link.runModule = function() {
    "use strict";
    Link.killExisting(function(err) {
        console.log(err);
        if (!Link.app.args.alone) {
            console.log("stating alarmManager");
            var child = require('child_process').spawn(
    	        'python',
                ["./alarmManager.py"],
    	        {cwd: __dirname}
            );
    	Link.started = true;
            child.on('close', function(code) {
    	        console.log(__dirname);
    	        Link.started = false;
                console.log('module ' + route + ' exit code ' + code);
                child = null;
            });

            return child;
        } else {
            return null;
        }
    });
};


Link.init = function(app) {
    "use strict";
    Link.app = app;
};

Link.emit = function(message, data) {
    if (data) {
        Link.pub.publish(route, JSON.stringify({
            message : message,
            data: data
        }));
        return;
    }
    Link.pub.publish(route, JSON.stringify({
        message : message
    }));
};

Link.setSocket = function() {
    "use strict";
	console.log("set socket alarm");
    Link.app.middleware.socketConnection.socket.on("alarm:updated", function(data) {
        console.log("alarms");
        console.log(data);
	    try {
		    Link.pub.publish(route, JSON.stringify({message: "alarm:updated", data: data.alarm}));
	    } catch(e) {
		    console.log(e);
	    }

    });
	Link.app.middleware.socketConnection.socket.on("alarms:new", function(data) {
        console.log("new alarm");
        console.log(data);
	    try {
		    Link.pub.publish(route, JSON.stringify({message: "alarms:new", data: data}));
	    } catch(e) {
		    console.log(e);
	    }

    });
    Link.app.middleware.socketConnection.socket.on("alarm:removed", function(data) {
        console.log("remove alarm");
        console.log(data);
        try {
            Link.pub.publish(route, JSON.stringify({message: "alarm:removed", data: data}));
        } catch(e) {
            console.log(e);
        }

    });
};

module.exports = Link;


