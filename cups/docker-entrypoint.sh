#!/bin/bash
# This file is used in the Dockerfile as the starting command for the run_celery target

set -e

useradd \
  --groups=lp,lpadmin \
  --create-home \
  --home-dir=/home/gutenberg \
  --shell=/bin/bash \
  --password="$(mkpasswd gutenberg)" \
  gutenberg

/usr/sbin/cupsd -f
