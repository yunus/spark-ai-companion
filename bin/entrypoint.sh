#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Set default values for Gunicorn workers if not provided by environment variables
# A common rule of thumb is (2 * number_of_cores) + 1
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}

echo "Starting the application server with Gunicorn and Uvicorn workers..."

# Start Gunicorn, which will in turn manage the Uvicorn workers
# -w: The number of worker processes
# -k: The type of worker to use. 'uvicorn.workers.UvicornWorker' is the key.
# -b: The address to bind to.
gunicorn -w "${GUNICORN_WORKERS}" -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8181 app.main:app
