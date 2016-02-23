var MQTT = require("./mqtt");


module.exports = function(app) {
    "use strict";
    var socket;
    var wasConnected = false;
    var connect = function(raspInfo, callback) {
        app.middleware.serverConnection.connectionToken().then(
            function(token) {
                var mqtt = new MQTT(raspInfo.name);
                mqtt.start(token, function(token, wasConnected) {
                    app.middleware.socketConnection.socket = mqtt;
                    callback(token, wasConnected);
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