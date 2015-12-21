var os = require('os');
var ifaces = os.networkInterfaces();

function getIpAddr() {
  var interfaces = {};
  Object.keys(ifaces).forEach(function (ifname) {
    var alias = 0;
    ifaces[ifname].forEach(function (iface) {
      if ('IPv4' !== iface.family || iface.internal !== false) {
        // skip over internal (i.e. 127.0.0.1) and non-ipv4 addresses
        return;
      }
      if (ifname && iface.address) {
        var fIfName = ifname
        if (alias >= 1) {
          fIfName += ":" + alias;
        }
        interfaces[fIfName] = iface.address;
      }
      ++alias;
    });
  });
  return interfaces;
}

module.exports = {
  getIpAddr: getIpAddr
}