var http = require('http');
var socketio = require('socket.io');
var express = require('express');
var request = require('request');
var bodyParser = require('body-parser');

var app = express();
var server = http.createServer(app);
var io = socketio(server);

app.use(bodyParser.json({limit: '1mb'}));

var validateNamespace = io.of('/import_validate');
validateNamespace.on('connection', connectionHandler);

function connectionHandler(socket) {
    socket.on('set_id', function (id) {
        socket.join(id);
    });
}

app.post('/import_validate', function (req, res) {
    res.json({'message':'ok'});

    var id = req.body.id;

    validateNamespace.to(id).emit('finished', {
        id : id,
        errors : req.body.errors
    });
});


var importNameSpace = io.of('/import');
importNameSpace.on('connection', function (socket) {
  socket.on('listen', function (importJobId) {
    socket.join(importJobId);
  });
});

app.post('/import/:importJobId', function (req, res) {
  var jobId = req.params.importJobId;
  res.json({
    message: 'ok',
    jobId: jobId,
  });

  importNameSpace.to(jobId).emit('event', req.body);
});

var exportNamespace = io.of('/export');
exportNamespace.on('connection', connectionHandler);

app.post('/export', function (req, res) {
    res.json({'message':'ok'});

    var id = req.body.id;

    exportNamespace.to(id).emit('finished', {
        id : id
    });
});

var buildNamespace = io.of('/build');
buildNamespace.on('connection', connectionHandler);

app.post('/build', function (req, res) {
    res.json({'message':'ok'});

    var oice_id = req.body.id;
    var id = req.body.batchId || oice_id;
    var message = req.body.message;
    var payload = {
      id : oice_id,
      title : req.body.title,
      url : req.body.url,
      message
    };
    buildNamespace.to(id).emit(message == 'ok' ? 'finished' : 'failed', payload);
});

var pollingTimer = setInterval(function() {
  request.post(process.env.MODMOD_TRIAL_URL || "http://modmod:6543/trial_hook", function (error, response, body) {
    // do nothing
  });
}, process.env.MODMOD_TRIAL_POLLING_INTERVAL || 3600000); //3600 * 1000

server.listen(process.env.MODMOD_SOCKETIO_PORT || 8082);
console.info("Listening on " + (process.env.MODMOD_SOCKETIO_PORT || 8082));
