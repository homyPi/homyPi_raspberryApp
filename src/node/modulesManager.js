var fs = require("fs");
var path = require("path");
var _ = require("lodash");

var MODULES_PATH = process.env.HOMYPI_MODULES_PATH;

module.exports = function(app) {
	"use strict";
	var modulesConfig = require("../../config.json").modules;
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
			if (modules[i].child && modules[i].child.kill) {
				console.log("killing " + modules[i].name);
				modules[i].child.kill();
			}
		}
		modules = [];
	};
	var runModules = function() {
		for (var i = 0; i < modules.length; i ++) {
			if (modules[i].runModule) {
				modules[i].child = modules[i].runModule();
			}
		}
	};
	var setupModules = function() {
		var error = null;
		console.log(app.args.modules);
		_.forEach(modulesConfig, function(conf) {
			var name = conf.name;
			var ignore = false;
			var missing = false;
			if (app.args.modules) {
				ignore = (app.args.modules.indexOf(name) === -1);
			}
			if (!ignore) {
				var linkPath = path.join(MODULES_PATH, name) + "/link.js";
				var configPath = path.join(MODULES_PATH, name) + "/config.json";
				var m;
				try {
					fs.statSync(linkPath);
					m = require(linkPath);
					m.config = require(configPath);
				} catch(e) {
					console.log(e.stack);
					return;
				}
				console.log("init " + name);
				m.init(app, modules);
				modules.push(m);
			} else {
				console.log("ignoring " + name);
			}
		});
		return error;
	};
	var setSockets = function() {
		for (var i = 0; i < modules.length; i ++) {
			if (modules[i].setSocket)
				modules[i].setSocket();
		}
	};
	var socketReconnected = function() {
		for (var i = 0; i < modules.length; i ++) {
			if (modules[i].emit)
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