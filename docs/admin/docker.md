# Deploying a Gutenberg instance with Docker
The Gutenberg project provides a Docker configuration to simplify the deployment on your server.

## Dockerfile modifications
We intend to publish container images based on the `Dockerfile` in the future. If your use-case requires modifications
to the `Dockerfile` we encourage you to create an issue in the Gutenberg's
[GitHub issue tracker](https://github.com/KSIUJ/gutenberg/issues/). This way we can ensure that the published images
are suitable for customized setups.

## Required images
Gutenberg requires configuring a PostgreSQL database, a Redis instance and a CUPS server.
All of them need to be accessible from the Django server and from the Celery worker.
They can be deployed as Docker containers or as standalone instances.

On top of that, three more containers are required to run Gutenberg:
**TODO**

## Configuration
**TODO**

## docker-compose.yml
The `docker-compose.yml` file provides an example Docker Compose configuration, which references the local `Dockerfile`
to build the required Docker images. You might need to modify it to fit your deployment.

## Creating a superuser
After starting all Docker containers, the command below can be used to create a superuser account.
`gutenberg-backend` is the name of the container running the Django server.
```bash
docker exec -it gutenberg-backend ./manage.py createsuperuser
```
