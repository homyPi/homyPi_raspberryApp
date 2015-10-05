var amqp = require('amqplib');
module.exports = function(app) {
    "use strict";
    var topic = "serverRequest.*";
    var exchange = "serverRequest";
    amqp.connect('amqp://localhost').then(function(conn) {
        process.once('SIGINT', function() { conn.close(); });
        return conn.createChannel().then(function(ch) {
            var ex = "serverRequest";
            var ok = ch.assertExchange(ex, 'topic', {durable: false});

            ok = ok.then(function() {
                return ch.assertQueue('servQueue', {exclusive: true});
            });

            ok = ok.then(function(qok) {
                var queue = qok.queue;
                ch.bindQueue(queue, ex, topic);
                return queue;
            });

            ok = ok.then(function(queue) {
                return ch.consume(queue, emit, {noAck: true});
            });

            var emit = function(message) {
                var response;
                console.log(" [x] %s:'%s'",
                    message.fields.routingKey,
                    message.content.toString());
                try{
                    var json = JSON.parse(message.content.toString());
                    console.log("emit " + json.message);
                    if (app.middleware.socketConnection.socket && app.middleware.socketConnection.socket.connected) {
                        app.middleware.socketConnection.socket.emit(json.message, json.data);
                        response = {"status": "SENDED"};
                        ch.sendToQueue(message.properties.replyTo,
                            new Buffer(JSON.stringify(response)));
                    } else {
                        response = {"status": "NOT_CONNECTED"};
                        ch.sendToQueue(message.properties.replyTo,
                            new Buffer(JSON.stringify(response)));
                    }
                } catch (e) {
                    console.log("unable to parse "+message);
                }
            };
            return ok.then(function() {
                console.log(' [*] Waiting for logs. To exit press CTRL+C.');
            });

        });
    }).then(null, console.warn);
};




