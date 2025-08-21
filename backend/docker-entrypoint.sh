#!/bin/bash
# This file is used in the Dockerfile as the starting command for the run_backend target

set -e

uv run python manage.py migrate
# TODO: Replace --access-logfile with proper logging
uv run gunicorn gutenberg.wsgi:application --bind 0.0.0.0:8000 --access-logfile -
