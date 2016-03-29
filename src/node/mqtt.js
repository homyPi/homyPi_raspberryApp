var mqtt = require("mqtt");
var Promise = require("bluebird");

var URL = require("url");


function MQTT(name, url, token) {
	this.name = name;
	this.connected = false;
	this.wasConnected = false;
	this.events = {};

    var objUrl = URL.parse(url);
    var url = "tcp://" + objUrl.hostname + ":3005/?clientId=" + token;
	this.client  = mqtt.connect(url, {
		reconnectPeriod: 5000
	});
	this.client.on('message', function (topic, message) {
		try {
			var json = JSON.parse(message.toString());
			if (this.events[json.event]) {
				this.events[json.event].map(function(fn) {
					fn(json.data);
				});
			}
		} catch(e) {
			console.log(e);
		}
	}.bind(this));

	this.on = function(event, callback) {
		console.log("new callback for " + event);
		if (!this.events[event])
			this.events[event] = [];
		this.events[event].push(callback);
	}

	this.emit = function(event, data, toServer) {
		var topic = "client:" + name;
		if (toServer)
			topic += ":server";
		var message = {
			event: event
		}
		if (data) 
			message.data =  data;
		try {
			console.log("publish on topic: " + topic + "  message : " + JSON.stringify(message, null, 2));
			this.client.publish(topic, JSON.stringify(message));
		} catch(e) {
			console.log(e.stack);
		}
	}

	this.start = function(token, connectedCallback) {
		this.connectedCallback = connectedCallback;
		this.token = token;
		return new Promise(function(resolve, reject) {
			this.client.on('connect', function () {
				console.log("connect");
				if (this.connected) return;
				this.onConnected()
					.then(resolve)
					.catch(reject);
			}.bind(this));
			this.client.on('offline', function () {
				console.log("offline");
				this.connected = false;
			}.bind(this));
		}.bind(this));
	}

	this.onConnected = function() {
		return new Promise(function(resolve, reject) {
			console.log("connected " + this.name);
			this.connected = true;
			this.client.subscribe("raspberry:" + this.name);
			this.connectedCallback(this.token, this.wasConnected);
			this.wasConnected = true;
			resolve();
		}.bind(this));
	}
}

module.exports = MQTT;