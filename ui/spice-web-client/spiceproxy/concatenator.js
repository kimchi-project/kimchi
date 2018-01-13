#!/usr/bin/env node

var fs = require('fs');
var path = require('path');

// change to parent directory so all paths are relative to the top dir
process.chdir(path.dirname(__dirname));

var targetFile = path.join(__dirname, 'spiceproxy.js');

var files = [
	'lib/utils.js',
	'spiceobjects/spiceobjects.js',
	'spiceobjects/generated/protocol.js',
	'lib/GlobalPool.js',
	'lib/GenericObjectPool.js',
	'spiceproxy/socket.js',
	'spiceproxy/globalpool.js',
	'lib/queue.js',
	'network/socketqueue.js',
	'network/packetextractor.js',
	'network/packetcontroller.js',
	'network/sizedefiner.js',
	'network/packetreassembler.js',
	'network/reassemblerfactory.js',
	'lib/biginteger.js',
	'spiceproxy/spicechannel.js'
];

var exportString = "\nmodule.exports = wdi; \n";

console.log("Will generate %s", targetFile);
if (fs.existsSync(targetFile)) {
	fs.unlinkSync(targetFile);
}

files.forEach(function (file) {
	var data = fs.readFileSync(file);
	console.log('... appending %s', file);
	fs.appendFileSync(targetFile, data);
});

console.log("Done! Appending module.exports line...");
fs.appendFileSync(targetFile, exportString);

console.log("Finish... Everything is stored in %s", targetFile);
