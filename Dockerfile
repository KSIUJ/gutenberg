# build_webapp target
#   Builds the static files for the web app
#
#   outputs:
#   - /app/webapp/.output/html - the generated HTML files for the SPA
#   - /app/webapp/.output/public - the generated static files for the SPA
FROM node:22-alpine AS build_webapp

# https://pnpm.io/docker
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable pnpm

WORKDIR /app/webapp

COPY webapp/package.json webapp/pnpm-workspace.yaml webapp/pnpm-lock.yaml /app/webapp/
RUN pnpm install --frozen-lockfile

COPY ./webapp /app/webapp/
RUN pnpm run build


# setup_base target
#   Install the binaries required for all Python images including Python and uv
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS setup_base

WORKDIR /app/backend

# https://docs.docker.com/build/building/best-practices/#apt-get
# Install pacakges required for installing uv and used by the backend server
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*


# setup_django target
#   Syncs the uv project and copies all backend project files
#
#   extends: setup_base
#   build outputs:
#   - /app/backend - the backend directory with the .venv set up by uv
FROM setup_base AS setup_django

COPY ./backend/pyproject.toml ./backend/uv.lock /app/backend/
RUN uv sync --no-managed-python
COPY ./backend /app/backend/


# collect_static target
#   Collects all the static files to be served under /static by NGINX
#
#   extends: setup_django
#   build inputs:
#   - /app/webapp/.output/public from build_webapp
#   build outputs:
#   - /app/staticroot - collected static files
FROM setup_django AS collect_static

ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_base
RUN mkdir /var/log/gutenberg
COPY --from=build_webapp /app/webapp/.output/public /app/webapp_public/
# collectstatic puts the collected static files into STATIC_ROOT,
# configured in docker_base_settings.py as /app/staticroot
RUN uv run python manage.py collectstatic --noinput


# run_backend target
#   Performs the Django database migration and starts a gunicorn server on port 8000
#
#   extends: setup_django
#   mounts:
#   - /var/log/gutenberg - the logs volume
#   - /var/lib/gutenberg - the data volume
#   - /etc/gutenberg/docker_settings.py (readonly)
#   exposes port 8000 for proxying by NGINX
FROM setup_django AS run_backend

RUN ln -s /etc/gutenberg/docker_settings.py /app/backend/gutenberg/settings/docker_settings.py
ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_server_overrides
ENTRYPOINT ["./docker-entrypoint.sh", "run-backend"]
VOLUME ["/var/log/gutenberg"]


# run_celery target
#   Installs binaries required for processing and printing and starts the Celery worker.
#
#   extends: setup_base
#   build inputs:
#   - /app/backend from setup_django
#   mounts:
#   - /var/log/gutenberg - the logs volume
#   - /var/lib/gutenberg - the data volume
#   - /etc/gutenberg/docker_settings.py (readonly)
FROM setup_base AS run_celery

# These apt-get install commands are time and space consuming, so they are run early in the build chain for `run_celery`.
# To avoid running `uv sync` twice and to benefit from layer catching for `uv sync`,
# the /app/backend directory (already containing the `.venv` created by running `uv sync`) is copied from setup_django.
# Making `run_celery` extend `setup_django` instead of copying files from it would work, but would usually be way
# slower, because the `apt-get install` command would run after every change in the `backend` directory.
#
# TODO: Consider installing some fonts recommended for libreoffice despite installing --no-install-recommends.
# TIP:  You can use the command
#       > apt-cache depends libreoffice
#       to check the required, recommended (installed unless --no-install-recommends is enabled) and suggested
#       (not installed by default) dependencies of the package.
#
# This step installs only cups-client (for the lp and cancel commands), not cups (which depends on cups-client).
# This means that the container can only be used with an external CUPS server.
# If needed, the user can deploy https://hub.docker.com/r/olbat/cupsd as a separate container.
# NOTE: The size of cups vs cups-client is not a problem, cups instead of cups-client increases the image size by about
#       17 MB.
# TIP:  Run this command to check which package provides the specified binary:
#       > dpkg -S $(which cancel)
#       outputs: "cups-client: /usr/bin/cancel"
#
RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick \
    ghostscript \
    pdftk \
    bubblewrap \
    cups-client \
    libreoffice \
  && rm -rf /var/lib/apt/lists/*

COPY --from=setup_django /app/backend /app/backend/

RUN ln -s /etc/gutenberg/docker_settings.py /app/backend/gutenberg/settings/docker_settings.py
ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_server_overrides
ENTRYPOINT ["./docker-entrypoint.sh", "run-celery"]
VOLUME ["/var/log/gutenberg"]


# run_nginx target
#   Runs the NGINX proxy.
#
#   build inputs:
#   - /app/webapp/.output/html from build_webapp
#   - /app/staticroot from collect_static
#   depends on run_backend for server on port 8000
#   exposes port 80 for public access
#
#   This image can be extended by adding configuration files to these directories:
#   - /etc/nginx/conf.d
#   - /etc/nginx/gutenberg-locations.d
#   As described in https://ksiuj.github.io/gutenberg/admin/docker.html
FROM nginx:alpine AS run_nginx

RUN rm /etc/nginx/conf.d/default.conf
COPY --from=build_webapp /app/webapp/.output/html /usr/share/nginx/gutenberg/webapp_html
# /app/staticroot is the value of STATIC_ROOT in docker_base_settings.py
COPY --from=collect_static /app/staticroot /usr/share/nginx/gutenberg/static
COPY nginx/gutenberg.conf /etc/nginx/conf.d/gutenberg.conf
COPY nginx/locations /etc/nginx/gutenberg-locations.d
EXPOSE 80
