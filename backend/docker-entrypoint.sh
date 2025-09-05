#!/bin/bash
# This file is used in the Dockerfile as the starting command for the run_backend and run_celery targets
# Use:
# - To start the Django server:
#   ./dokcer-entrypoint.sh run-backend
# - To start the Celery worker:
#   ./docker-entrypoint.sh run-celery

set -e

# Create app user if it doesn't exist
if ! id "appuser" &>/dev/null; then
    useradd -r -s /bin/false appuser
    echo "Created appuser"
fi

# Set up permissions for both backend and celery
setup_permissions() {
    # Create log directory if it doesn't exist and set proper permissions
    mkdir -p /var/log/gutenberg
    chown -R appuser:appuser /var/log/gutenberg
    
    # Change ownership of app directory
    chown -R appuser:appuser /app
}

case "$1" in
 run-backend)
    setup_permissions
    
    # Run migrations as appuser
    runuser -u appuser -- env UV_CACHE_DIR=/app/.cache/uv uv run python manage.py migrate
    
    # Run gunicorn as appuser
    # TODO: Replace --access-logfile with proper logging
    runuser -u appuser -- env UV_CACHE_DIR=/app/.cache/uv uv run gunicorn gutenberg.wsgi:application --bind 0.0.0.0:8000 --access-logfile -
    ;;
 run-celery)
    setup_permissions
    
    # Run Celery as appuser
    runuser -u appuser -- env UV_CACHE_DIR=/app/.cache/uv uv run celery -A gutenberg worker -l INFO
    ;;
 *)
    echo "Error: Missing or invalid first argument to docker-entrypoint.sh: '$1'."
    exit 1
    ;;
esac