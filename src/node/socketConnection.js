var io = require('socket.io-client');



module.exports = function(app) {
    "use strict";
    var socket;
    var wasConnected = false;
    var connect = function(callback) {
        app.middleware.serverConnection.connectionToken().then(
            function(token) {
                console.log("creating socket");
                socket = io.connect(app.settings.host, {
                    'query' : 'token=' + token
                });
                socket.on('connect', function() {
                    socket.emit("pi:login", {
                        "name" : "rasp1",
                        "ip" : "92.68.1.0"
                    });
                    console.log("connected");
                    app.middleware.socketConnection.socket = socket;
                    callback(token, wasConnected);
                    wasConnected = true;
                });
                socket.on("error", function(error) {
                    console.log(error);
                    if (error.type === "UnauthorizedError" || error.code === "invalid_token") {
                        reconnect(callback);
                    } else {
                        console.log(error);
                    }
                });
                socket.on('disconnect', function() {
                    console.log("disconnected");
                });
            });
    };

    var reconnect = function(callback) {
        console.log("reconnecting...");
        if (socket) {
            socket.disconnect();
        }
        connect(callback);
    };
    app.middleware.socketConnection = {
        connect: connect,
        reconnect: reconnect,
        socket: socket
    };
}