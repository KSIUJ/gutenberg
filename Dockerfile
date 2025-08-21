# build_webapp target
#   Builds the web app
#
#   outputs:
#   - /app/dist - the generated static files for the SPA
FROM node:16-alpine AS build_webapp

WORKDIR /app

COPY package.json yarn.lock /app/
RUN yarn install

# TODO: When https://github.com/KSIUJ/gutenberg/pull/86 is merged, copy only the webapp directory
COPY vue.config.js babel.config.js .eslintrc.js .browserslistrc /app/
COPY ./webapp /app/webapp/
RUN yarn build


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
#   build outputs:
#   - /app/staticroot - collected static files
FROM setup_django AS collect_static

ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_base_settings
RUN mkdir /var/log/gutenberg
COPY --from=build_webapp /app/dist /app/webapp_dist/
# collectstatic puts the collected static files into STATIC_ROOT,
# configured in docker_base_settings.py as /app/staticroot
RUN uv run python manage.py collectstatic --noinput


# run_backend target
#   Performs the Django database migration and starts a gunicorn server on port 8000
#
#   extends: setup_django
#   mounts:
#   TODO: Change local mounts, a link could be created to support docker_settings.py
#   - /var/log/gutenberg - the logs volume
#   - /app/backend/gutenberg/settings/docker_settings.py
#   exposes port 8000 for proxying by NGINX
FROM setup_django AS run_backend

ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_settings
CMD ["./docker-entrypoint.sh"]
VOLUME ["/var/log/gutenberg"]


# run_celery target
#   Installs binaries required for processing and printing and starts the Celery worker.
#
#   extends: setup_base
#   build inputs:
#   - /app/backend from setup_django
#   mounts:
#   TODO: Change local mounts, a link could be created to support docker_settings.py
#   - /var/log/gutenberg - the logs volume
#   - /app/backend/gutenberg/settings/docker_settings.py
FROM setup_base AS run_celery

# This command is time and space consuming, so it's run early in the build chain for `run_celery`.
# To avoid running `uv sync` twice and to benefit from layer catching for `uv sync`,
# the /app/backend (already containing the `.venv` created by running `uv sync`) is copied from setup_django.
# Making `run_celery` extend `setup_django` instead of copying files from it would work, but would usually be way
# slower, because the `apt-get install` command would run after every change in the `backend` directory.
RUN apt-get update && apt-get install -y \
    imagemagick \
    ghostscript \
    pdftk \
    bubblewrap \
    cups \
    libreoffice \
  && rm -rf /var/lib/apt/lists/*

COPY --from=setup_django /app/backend /app/backend/

ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_settings
CMD ["uv", "run", "celery", "-A", "gutenberg", "worker", "-l", "INFO"]
VOLUME ["/var/log/gutenberg"]


# run_nginx target
#   Runs the NGINX proxy.
#
#   build inputs:
#   - /app/staticroot from collect_static
#   depends on run_backend for server on port 8000
#   exposes port 80 for public access
FROM nginx:alpine AS run_nginx

# /app/staticroot is the value of STATIC_ROOT in docker_base_settings.py
COPY --from=collect_static /app/staticroot /usr/share/nginx/html/static
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
