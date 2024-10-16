#!/bin/sh

# here we replace the environment variables
# provided to the docker container by generating a new temporary file.
# then we replace the original env file.


envsubst < /home/app/.env.temp > /home/app/.env

exec "$@"