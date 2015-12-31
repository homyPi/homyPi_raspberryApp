var path = require("path");
var ps = require("ps-node");

var Link = function() {};
Link.app = {
	args: {}
};

Link.init = function(app, modules) {
    "use strict";
    Link.app = app;

    for(var i = 0; i < modules.length; i++) {
        if (modules[i].config.name === "player_base") {
            modules[i].addPlayer("spotify", "SpotifyPlayer", path.join(process.env.HOMYPI_MODULES_PATH, "spotify/spotify_player.py"));
            break;
        }
    }
};
module.exports = Link;


