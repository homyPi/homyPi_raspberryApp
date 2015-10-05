var Promise = require("bluebird");
var request = require("request");

var TIMEOUT = 30000;
var RETRY_TIMEOUT = 5000;
var app = {};

module.exports = function(app) {
	"use strict";
	var token;
	var handleBody = function (body) {
		return new Promise(function(resolve, reject) {
			try {
				var json = JSON.parse(body);
				if (json && json.token) {
					token = json.token;
					resolve(token);
				} else {
					reject("invalid data");
				}
			} catch (e) {
				console.log(e + " on parsing " + body);
				reject(e);
			}
		});
	};

	var getToken = function () {
		return new Promise(function(resolve, reject) {
			console.log("trying to get token at " + app.settings.host + "/user/login/token");
			request(
				{
					url: app.settings.host + '/api/users/login',
					method: 'POST',
					form: {
						username: app.settings.username,
						password: app.settings.password,
						isRaspberry: true
					},
					followAllRedirects: true,
					timeout: TIMEOUT
				},
				function (err, resp, body) {
					if (err) {
						console.log(err);
						reject(err);
					} else {
						handleBody(body).then(
							function (token) {
								resolve(token);
							}, function (err) {
								console.log(err);
								reject(err);
							});
					}
				});
		})
	};


	var connectionToken = function () {
		return new Promise(function(resolve, reject) {
		token = null;
		getToken().then(
			function (token) {
				console.log("got token " + token);
				resolve(token);
			}, function (err) {
				setTimeout(function () {
						connectionToken().then(resolve);
					}, RETRY_TIMEOUT);
			});
		})
	};

	app.middleware.serverConnection = {
		connectionToken: connectionToken
	};
};