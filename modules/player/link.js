var route = "module.player";
var path = require("path");
var ps = require("ps-node");
var rabbit = require('rabbit.js');

var Link = function() {};
Link.app = {
	args: {}
};
Link.players = [];
Link.sub = null;
Link.pub = null;

Link.context = rabbit.createContext();
Link.context.on('ready', function() {
Link.pub = Link.context.socket('PUBLISH', {routing: "direct"});
Link.pub.connect(route, function() {
    console.log("player pub ready");
    Link.pub.on("error", function(err) {
        console.log(err);
        })
    });
});
Link.killExisting = function(callback) {
    console.log("killing existing modules");
    ps.lookup({
        command: "homyPi_player", psargs: 'ux'
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
        console.log("Link.app.args.alone = " + Link.app.args.alone);
        console.log("players = ", JSON.stringify(Link.players, null, 2));
        if (!Link.app.args.alone) {
            var playersStr = JSON.stringify(Link.players);
            console.log("stating player.py --players '" + playersStr + "'");
            var child = require('child_process').spawn(
    	        'python',
                [ "./playerManager.py", "--players", "" + playersStr + ""],
    	        {cwd: __dirname}
            );
            child.on('close', function(code) {
                console.log('module ' + route + ' exit code ' + code);
                child = null;
            });

            return child;
        } else {
            return null;
        }
    });
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


Link.init = function(app) {
    "use strict";
    Link.app = app;
};
Link.setSocket = function() {
    "use strict";
    console.log("set player socket listeners")
    Link.app.middleware.socketConnection.socket.on("player:play:track", function(data) {
        console.log(" server response resume", data, route);
        Link.pub.publish(route, JSON.stringify({
            message : "playTrack",
            data: data
        }));
    });
    Link.app.middleware.socketConnection.socket.on("player:play:trackset", function(data) {
        console.log(" server response resume");
        Link.pub.publish(route, JSON.stringify({
            message : "playListSet",
            data: data
        }));
    });
    //
    Link.app.middleware.socketConnection.socket.on("player:resume", function() {
        console.log(" server response resume");
        Link.pub.publish(route, JSON.stringify({
            message : "resume"
        }));
    });
    Link.app.middleware.socketConnection.socket.on("player:pause", function() {
        console.log("server response pause");
        Link.pub.publish(route, JSON.stringify({
            message : "pause"
        }));
    });
    Link.app.middleware.socketConnection.socket.on("player:next", function() {
        console.log("player next");
        Link.pub.publish(route, JSON.stringify({
            message : "next"
        }));
    });
    Link.app.middleware.socketConnection.socket.on("player:previous", function() {
         console.log("player previous");
        Link.pub.publish(route, JSON.stringify({
            message : "previous"
        }));
    });
    Link.app.middleware.socketConnection.socket.on("player:playlist:add", function(data) {
        Link.pub.publish(route, JSON.stringify({
            message : "playListAdd",
            data : data
        }));
    });
    Link.app.middleware.socketConnection.socket.on("music:playlist:get", function(data) {
        if (data.status === "success") {
            console.log("got server response for music:playlist:get");
            Link.pub.publish(route, JSON.stringify({
                message : "playListInit",
                data : data
            }));
        }
    });
    Link.app.middleware.socketConnection.socket.on("music:playlist:set", function(data) {
        Link.pub.publish(route, JSON.stringify({
            message : "playListSet",
            data : data
        }));
    });
    Link.app.middleware.socketConnection.socket.on("music:playlist:playing:id", function(data) {
        Link.pub.publish(route, JSON.stringify({
            message : "playIdInPlaylist",
            data : data
        }));
    });
    Link.app.middleware.socketConnection.socket.on("player:playlist:remove", function(data) {
        Link.pub.publish(route, JSON.stringify({
            message : "removeInPlaylist",
            data : data
        }));
    });
    Link.app.middleware.socketConnection.socket.on("player:seek", function(data) {
        Link.pub.publish(route, JSON.stringify({
            message : "seek",
            data : data
        }));
    });
    Link.app.middleware.socketConnection.socket.on("player:volume:set", function(data) {
        Link.pub.publish(route, JSON.stringify({
            message : "setVolume",
            data : data
        }));
    });
};

Link.addPlayer = function(moduleName, className, path) {
    Link.players.push({
        moduleName: moduleName,
        className: className,
        path: path
    });
}

module.exports = Link;


