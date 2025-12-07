#!/bin/bash

VERSION=$(poetry version --short)

# Build the Docker image
docker build -t saerco/vlas-server:${VERSION} -f docker/server/Dockerfile . 

docker build -t saerco/vlas-client:${VERSION} -f docker/client/Dockerfile .
