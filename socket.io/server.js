const http = require('http');
const socketio = require('socket.io');
const express = require('express');
const request = require('request');
const bodyParser = require('body-parser');

const app = express();
const server = http.createServer(app);
const io = socketio(server);

app.use(bodyParser.json({ limit: '1mb' }));

function connectionHandler(socket) {
  socket.on('set_id', (id) => {
    socket.join(id);
  });
}

const validateNamespace = io.of('/import_validate');
validateNamespace.on('connection', connectionHandler);

app.post('/import_validate', (req, res) => {
  res.json({ message: 'ok' });

  const { id } = req.body;

  validateNamespace.to(id).emit('finished', {
    id,
    errors: req.body.errors,
  });
});

const importNameSpace = io.of('/import');
importNameSpace.on('connection', (socket) => {
  socket.on('listen', (importJobId) => {
    socket.join(importJobId);
  });
});

app.post('/import/:importJobId', (req, res) => {
  const jobId = req.params.importJobId;
  res.json({
    message: 'ok',
    jobId,
  });

  importNameSpace.to(jobId).emit('event', req.body);
});

const exportNamespace = io.of('/export');
exportNamespace.on('connection', connectionHandler);

app.post('/export', (req, res) => {
  res.json({ message: 'ok' });

  const { id } = req.body;

  exportNamespace.to(id).emit('finished', {
    id,
  });
});

const buildNamespace = io.of('/build');
buildNamespace.on('connection', connectionHandler);

app.post('/build', (req, res) => {
  res.json({ message: 'ok' });

  const oiceId = req.body.id;
  const id = req.body.batchId || oiceId;
  const { message } = req.body;
  const payload = {
    id: oiceId,
    title: req.body.title,
    url: req.body.url,
    message,
  };
  buildNamespace.to(id).emit(message === 'ok' ? 'finished' : 'failed', payload);
});

const addAudioNameSpace = io.of('/audio/convert');
addAudioNameSpace.on('connection', (socket) => {
  socket.on('listen', (jobId) => {
    socket.join(jobId);
  });
});

app.post('/audio/convert/:jobId', (req, res) => {
  const { jobId } = req.params;
  res.json({
    message: 'ok',
    jobId,
  });

  addAudioNameSpace.to(jobId).emit('event', req.body);
});

setInterval(() => {
  request.post(process.env.MODMOD_TRIAL_URL || 'http://modmod:6543/trial_hook', (error) => {
    if (error) console.error(error); // do nothing
  });
}, process.env.MODMOD_TRIAL_POLLING_INTERVAL || 3600000); // 3600 * 1000

server.listen(process.env.MODMOD_SOCKETIO_PORT || 8082);
console.info(`Listening on ${process.env.MODMOD_SOCKETIO_PORT || 8082}`);
