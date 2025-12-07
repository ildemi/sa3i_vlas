#!/bin/bash
docker compose -f docker/docker-compose.yml --project-name vlas --env-file .env  up
