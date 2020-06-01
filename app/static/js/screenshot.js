var system = require('system');
var page = require('webpage').create();

var address, outfile, width, height, clip_height;

address = system.args[1];
outfile = system.args[2];
width = 1024; height = 800;
if (system.args.length > 3) {
  clip_height = parseInt(system.args[3]);
} else {
  clip_height = 800;
}

page.viewportSize = { width: width, height: height };

if (clip_height) {
  page.clipRect = { width: width, height: clip_height };
}

window.setTimeout(function() {
  phantom.exit(2);
}, 30000);

page.open(address, function (status) {
  if (status !== 'success') {
    console.log('Unable to load the address!');
    phantom.exit(1);
  } else {
    window.setTimeout(function () {
      page.render(outfile);
      phantom.exit();
    }, 5000);
  }
});