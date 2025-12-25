#!/bin/bash
# View logs

docker-compose -f docker-compose.production.yml logs -f "$@"
