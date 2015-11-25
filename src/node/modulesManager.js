var fs = require("fs");
var path = require("path");
var _ = require("lodash");

var MODULES_PATH = path.join(__dirname, "../modules/");

module.exports = function(app) {
	"use strict";
	var modulesName = fs.readdirSync(MODULES_PATH);
	var modules = [];
	var route = "module.*";
	var context = require('rabbit.js').createContext();
	var pub;
	var sub;
	context.on('ready', function() {
		pub = context.socket('PUBLISH', {routing: "topic"}), sub = context.socket('SUBSCRIBE', {routing: "topic"});
		console.log("connecting to " + route);
		sub.connect(route, route, function() {
			pub.connect(route, function() {

			});
		});
	});

	var onConnected = function() {
		pub.publish(route, JSON.stringify({message: "connectedToServer"}));
	};

	var killAll = function() {
		for (var i = 0; i < modules.length; i ++) {
			if (modules[i].child) {
				console.log("killing " + modules[i].name);
				modules[i].child.kill();
			}
		}
		modules = [];
	};
	var runModules = function() {
		for (var i = 0; i < modules.length; i ++) {
			modules[i].child = modules[i].runModule();
		}
	};
	var setupModules = function() {
		var error = null;
		console.log(app.args.modules);
		_.forEach(modulesName, function(name) {
			var ignore = false;
			if (app.args.modules) {
				ignore = (app.args.modules.indexOf(name) === -1);
			}
			if (!ignore) {
				var linkPath = path.join(MODULES_PATH, name) + "/link.js";
				var m;
				try {
					fs.statSync(linkPath);
					m = require(linkPath);
				} catch (e) {
					error = e;
					return false;
				}
				console.log("init " + name);
				m.init(app);
				modules.push(m);
			} else {
				console.log("ignoring " + name);
			}
		});
		return error;
	};
	var setSockets = function() {
		for (var i = 0; i < modules.length; i ++) {
			modules[i].setSocket();
		}
	};
	var socketReconnected = function() {
		for (var i = 0; i < modules.length; i ++) {
			modules[i].emit("reconnected");
		}
	}
	app.middleware.modulesManager = {
		setSockets: setSockets,
		runModules: runModules,
		setupModules: setupModules,
		killAll: killAll,
		onConnected: onConnected,
		socketReconnected: socketReconnected
	};
};