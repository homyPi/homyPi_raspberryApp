var route = "module.notifier";
var path = require("path");
var ps = require("ps-node");
var rabbit = require('rabbit.js');

var Link = function() {};
Link.app = {
	args: {}
};
Link.notifiers = [];
Link.killExisting = function(callback) {
    console.log("killing existing modules");
    ps.lookup({
        command: "homyPi_notifier", psargs: 'ux'
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
        if (!Link.app.args.alone) {
            var notifiersStr = JSON.stringify(Link.notifiers);
            console.log("stating notifier.py --notifiers '" + notifiersStr + "'");
            var child = require('child_process').spawn(
    	        'python',
                [ "./notifier.py", "--notifiers", "" + notifiersStr + ""],
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

Link.init = function(app) {
    "use strict";
    Link.app = app;
};

Link.addNotifier = function(moduleName, className, path) {
    Link.notifiers.push({
        moduleName: moduleName,
        className: className,
        path: path
    });
}

module.exports = Link;


