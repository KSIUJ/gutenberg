#!/bin/bash
# This file is used in the Dockerfile as the starting command for the run_celery target

set -e

echo "gutenberg:$(cat /run/secrets/gutenberg_cups_password)" | chpasswd

/usr/sbin/cupsd -f
