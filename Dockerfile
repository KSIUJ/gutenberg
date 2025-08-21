FROM node:16-alpine AS build_webapp

WORKDIR /app

COPY package.json yarn.lock /app/
RUN yarn install

# TODO: When https://github.com/KSIUJ/gutenberg/pull/86 is merged, copy only the webapp directory
COPY vue.config.js babel.config.js .eslintrc.js .browserslistrc /app/
COPY ./webapp /app/webapp
RUN yarn build


# TODO: uv downloaded another Python version due to a mismatch in the version provided by the Docker image and
#       the one expected (from pyproject.toml)
FROM python:3.11-slim-bullseye AS setup_django

# https://docs.docker.com/build/building/best-practices/#apt-get
# Install pacakges required for installing uv and used by the backend server
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    build-essential \
    curl \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Install packages required for the document processing and printing
# TODO: This command should only be used in run_celery/
#       The instalation should however happen as early as possible.
#       This requires spiting the targets even more
RUN apt-get update && apt-get install -y \
    imagemagick \
    ghostscript \
    pdftk \
    bubblewrap \
    cups \
    libreoffice \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# uv is installed in /root/.local/bin, add it to PATH
ENV PATH="/root/.local/bin:${PATH}"

ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_base_settings
RUN mkdir /var/log/gutenberg

WORKDIR /app/backend

COPY ./backend/pyproject.toml ./backend/uv.lock /app/backend/
RUN uv sync

COPY ./backend /app/backend

VOLUME ["/var/log/gutenberg"]


FROM setup_django AS collect_static

COPY --from=build_webapp /app/dist /app/webapp_dist
# collectstatic puts the collected static files into STATIC_ROOT, configured in docker_base_settings.py.
# The STATIC_ROOT is copied in the run_nginx target
RUN uv run python manage.py collectstatic --noinput


FROM setup_django AS run_backend

ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_settings
CMD ["./docker-entrypoint.sh"]
VOLUME ["/var/log/gutenberg"]


FROM setup_django AS run_celery

CMD ["uv", "run", "celery", "-A", "gutenberg", "worker", "-l", "INFO"]
VOLUME ["/var/log/gutenberg"]


FROM nginx:alpine AS run_nginx

# /app/staticroot is the value of STATIC_ROOT in docker_base_settings.py
COPY --from=collect_static /app/staticroot /usr/share/nginx/html/static
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
