FROM node:16-alpine AS build_webapp

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install

COPY . .
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

# Dodaj uv do ścieżki
ENV PATH="/root/.local/bin:${PATH}"

ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_base_settings
RUN mkdir /var/log/gutenberg

WORKDIR /app

COPY ./ /app

RUN uv sync

COPY --from=build_webapp /app/dist /app/webapp_dist
RUN uv run python manage.py collectstatic --noinput
# collectstatic puts the collected static files into STATIC_ROOT

FROM setup_django AS run_server
ENV DJANGO_SETTINGS_MODULE=gutenberg.settings.docker_settings
# TODO: This might be unnecessary if the command is set in docker-compose.yml
CMD ["uv", "run", "gunicorn", "gutenberg.wsgi:application", "--bind", "0.0.0.0:8000"]
VOLUME ["/var/log/gutenberg"]

FROM nginx:alpine AS run_nginx

# TODO: Replace STATIC_ROOT with the value set in settings
COPY --from=setup_django /app/staticroot /usr/share/nginx/html/static
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80