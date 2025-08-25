#!/bin/bash
# This file is used in the Dockerfile as the starting command for the run_backend and run_celery targets
# Use:
# - To start the Django server:
#   ./dokcer-entrypoint.sh run-backend
# - To start the Celery worker:
#   ./docker-entrypoint.sh run-celery

set -e

case "$1" in
  run-backend)
    uv run python manage.py migrate
    # TODO: Replace --access-logfile with proper logging
    uv run gunicorn gutenberg.wsgi:application --bind 0.0.0.0:8000 --access-logfile -
    ;;

  run-celery)
    uv run celery -A gutenberg worker -l INFO
    ;;

  *)
    echo "Error: Missing or invalid first argument to docker-entrypoint.sh: '$1'."
    exit 1
    ;;
esac


