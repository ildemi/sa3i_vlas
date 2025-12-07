#!/bin/bash
docker compose --env-file .env -f docker/docker-compose.yml  --project-name vlas $@
