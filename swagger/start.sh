#!/usr/bin/env bash

PWD=`pwd`
WD=`cd $(dirname "$0") && pwd -P`
PORT=9876

cd "${WD}"

cleanup()
{
	cd "${PWD}"
}

main()
{
	./stop.sh

	# Container
    docker run -d -p ${PORT}:${PORT} --name "swagger-ui-builder" swagger-ui-builder
    echo "Swagger UI running at localhost:${PORT}"

	cleanup
}

main "${@}"
