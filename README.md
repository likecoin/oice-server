Oice-server(modmod) README
==================
[![CircleCI](https://circleci.com/gh/likecoin/oice-server.svg?style=svg)](https://circleci.com/gh/likecoin/oice-server)

- [Basic version](#basic-version)
- [Python Server](#python-server)
- [DB Migration commans](#db-migration-commands)
- [Import / Export worker](#import-export-worker)
- [Seed](#seed)
- [Suggested Dev Setup](#suggested-dev-setup)
- [Building docker image for use in oice/kubernetes](#building-docker-image-for-use-in-oice-kubernetes)
- [Swagger UI with modmod.yaml](#swagger-ui-with-modmod.yaml)
  - [Docker Image](#docker-image)
  - [Start Swagger UI](#start-swaggerui)
  - [Stop Swagger UI](#stop-swaggerui)

Oice-server(modmod) project consist of 

Basic version
-------------
- Python3.4+
- Assume Maria10.0 +
- Redis3.0+
- nodejs v0.12+
- pip 1.5.6+ (Other version specific at requirements.pip)
- Assuming `unzip` and `zip` is avalible. (nots ubuntu is not installed by
  default)

Python Server
---------------
How to run the python 
- `cd <directory containing this file>`
- `$VENV/bin/python setup.py develop`
- `$VENV/bin/pserve development.ini`

DB Migration commands
---------------------
- Create a migration:
    `alembic -c development.ini revision -m "new table"`

- Running migrations:
    `alembic [-c development.ini] upgrade head`

- Downgrade migration:
    `alembic [-c development.ini] downgrade -1`

Import / Export worker
-----------------------
In Import/Export workflow, you will need to open the pubsub server to get
notified with the long runing process.

- Run the worker

    `rqworker`

- Run Redis, refs: http://redis.io/download

    `redis-server`

- Run Socket.io

    Install the deps `(socket.io) npm install`
    `node socket.io/server.js`

Seed
-----
- After running setup.py
- Add default tags to database `initialize_modmod_db`
- Add dummy projects and ks files `modmod_load_dummy`

Suggested Dev Setup
-------------------
- Please refer to [oice repository](https://github.com/lakoo/oice-deployment) README.md

## Building docker image for use in oice/kubernetes
```bash
$ ./build.sh
```

pserve image will be tagged as `modmod`

socket.io image will be tagged as `modmod-socket`

## Swagger UI with modmod.yaml
The set up will copy swagger/yaml/modmod.yaml to docker image. Swagger UI is hosted on localhost:9876.

### Docker Image
To create the docker image of Swagger UI, in swagger/, run:
```bash
./build.sh
```

### Start Swagger UI
To start Swagger UI, in `./swagger/`, run:
```bash
./start.sh
```

### Stop Swagger UI
To stop Swagger UI, in `./swagger/`, run:
```bash
./stop.sh
```
