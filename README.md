Oice-server(modmod) README
==================

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
- modify your /etc/hosts to map modmod.dev to 127.0.0.1
- Use nginx as reserve proxy, example see `nginx.conf.example`. Ensure the nginx
  version support ws upgrade. i.e. 1.3+
- Use supervisord to open all the services, example see `supervisord.conf.sample`
    - please note that supervisord is py2, you need a separate virtualenv.
- You may `tail -f logs/*` for monitor log

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
