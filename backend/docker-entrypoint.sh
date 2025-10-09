#!/bin/bash
# This file is used in the Dockerfile as the starting command for the run_backend and run_celery targets
# Use:
# - To start the Django server:
#   ./dokcer-entrypoint.sh run-backend
# - To start the Celery worker:
#   ./docker-entrypoint.sh run-celery

set -e

# Create app user if it doesn't exist
if ! id "$GUTENBERG_USERNAME" &>/dev/null; then
    if ! getent group "${GUTENBERG_GID}" &>/dev/null; then
        groupadd --system --gid "${GUTENBERG_GID}" "${GUTENBERG_USERNAME}"
        echo "Created group $GUTENBERG_USERNAME with GID $GUTENBERG_GID"
    fi

    useradd --system --shell /bin/false "$GUTENBERG_USERNAME" --uid "$GUTENBERG_UID" --gid "$GUTENBERG_GID"
    echo "Created user $GUTENBERG_USERNAME with UID $GUTENBERG_UID"
fi

# Verify user UID and GID
actual_uid=$(id -u "${GUTENBERG_USERNAME}")
actual_gid=$(id -g "${GUTENBERG_USERNAME}")
if [[ "${actual_uid}" != "${GUTENBERG_UID}" || "${actual_gid}" != "${GUTENBERG_GID}" ]]; then
    echo "Error: The existing user $GUTENBERG_USERNAME has a different UID or GID than the one specified in the env variables GUTENBERG_UID and GUTENBERG_GID."
    echo "Expected UID: ${GUTENBERG_UID}, actual: ${actual_uid}"
    echo "Expected GID: ${GUTENBERG_UID}, actual: ${actual_gid}"
    exit 1
fi

if [ -d /run/cups/cups.sock ]; then
  echo "Warning: /run/cups/cups.sock is mounted as a directory, not a socket."
  echo "It likely means that Docker was not able to locate the source file."
  echo "This issue can occur when using Docker Desktop, please refer to the Docker deployment chapter of Gutenberg docs for more information."

  exit 1
fi

# Set up permissions for both backend and celery
setup_permissions() {
    # Create required directories if they don't exist and set proper permissions
    mkdir -p /var/log/gutenberg /var/lib/gutenberg
    chown -R "$GUTENBERG_UID:$GUTENBERG_GID" /var/log/gutenberg /var/lib/gutenberg

    # Change ownership of app directory
    chown -R "$GUTENBERG_UID:$GUTENBERG_GID" /app
}

case "$1" in
 run-backend)
    setup_permissions

    # Run migrations as $GUTENBERG_USERNAME
    runuser -u "$GUTENBERG_USERNAME" -- env UV_CACHE_DIR=/app/.cache/uv uv run python manage.py migrate

    # Run gunicorn as $GUTENBERG_USERNAME
    runuser -u "$GUTENBERG_USERNAME" -- env UV_CACHE_DIR=/app/.cache/uv uv run gunicorn gutenberg.wsgi:application --bind 0.0.0.0:8000 --access-logfile -
    ;;
 run-celery)
    setup_permissions

    # Run Celery as "$GUTENBERG_USERNAME"
    runuser -u "$GUTENBERG_USERNAME" -- env UV_CACHE_DIR=/app/.cache/uv uv run celery -A gutenberg worker -l INFO
    ;;
 *)
    echo "Error: Missing or invalid first argument to docker-entrypoint.sh: '$1'."
    exit 1
    ;;
esac
