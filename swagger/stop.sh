#!/usr/bin/env bash

PWD=`pwd`
WD=`cd $(dirname "$0") && pwd -P`

cd "${WD}"

printf "Killing 'swagger-ui-builder' ... "
docker kill swagger-ui-builder &> /dev/null
docker rm swagger-ui-builder &> /dev/null
echo 'DONE'

cd "${PWD}"
