FROM node:16-alpine AS build_webapp

WORKDIR /app

COPY package.json yarn.lock /app/
RUN yarn install

# TODO: When https://github.com/KSIUJ/gutenberg/pull/86 is merged, copy only the webapp directory
COPY vue.config.js babel.config.js .eslintrc.js .browserslistrc /app/
COPY ./webapp /app/webapp
RUN yarn build


FROM python:3.11-slim-bullseye AS setup_django

RUN apt-get update && apt-get install -y \
    imagemagick \
    ghostscript \
    pdftk \
    bubblewrap \
    build-essential \
    curl \
    libpq-dev \
    cups \
    libreoffice \
    libmagic1 \
    libmagic-dev \
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

COPY --from=build_webapp /app/dist /app/webapp_dist
# collectstatic puts the collected static files into STATIC_ROOT, configured in docker_base_settings.py.
# The STATIC_ROOT is copied in the run_nginx target
RUN uv run python manage.py collectstatic --noinput
RUN rm -r /app/webapp_dist

VOLUME ["/var/log/gutenberg"]

FROM setup_django AS run_server
ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_settings
# TODO: This might be unnecessary if the command is set in docker-compose.yml
CMD ["uv", "run", "gunicorn", "gutenberg.wsgi:application", "--bind", "0.0.0.0:8000"]
VOLUME ["/var/log/gutenberg"]

FROM nginx:alpine AS run_nginx

# /app/staticroot is the value of STATIC_ROOT in docker_base_settings.py
COPY --from=setup_django /app/staticroot /usr/share/nginx/html/static
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
