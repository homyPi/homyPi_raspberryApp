var path = require("path");

var Link = function() {};
Link.app = {
	args: {}
};

Link.init = function(app, modules) {
    "use strict";
    Link.app = app;

    for(var i = 0; i < modules.length; i++) {
        if (modules[i].config.name === "notifier") {
        	console.log(modules[i]);
        	try {
            modules[i].addNotifier("ttsx", "TtsxNotifier", path.join(process.env.HOMYPI_MODULES_PATH, "ttsxNotifier/ttsxNotifier.py"));
        }catch(e) {console.log(e.stack)}
            break;
        }
    }
};
module.exports = Link;


