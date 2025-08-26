
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

the Django backend server, the Celery worker for executing background tasks, and the Nginx proxy that routes incoming HTTP requests and serves static files.

In summary:
| Container name       | Description                                      |
|:-------------------- |:------------------------------------------------ |
| `gutenberg-cups`     | CUPS server for managing print jobs              |
| `gutenberg-db`       | PostgreSQL database for storing application data |
| `gutenberg-redis`    | Redis instance for caching and task queue        |
| `gutenberg-backend`  | Django application server                        |
| `gutenberg-celery`   | Celery worker for background tasks               |
| `gutenberg-proxy`    | Nginx for routing requests                       |

## Configuration

In order to run Gutenberg in Docker, you need to make your own version of the settings:
  ```bash
  cp backend/gutenberg/settings/docker_settings.py.example backend/gutenberg/settings/docker_settings.py
```
In `docker_settings.py`, fill in the following fields properly:
* `SECRET_KEY` - unique random string 
* `ALLOWED_HOSTS` - list of hosts that can connect to the app
*  `CSRF_TRUSTED_ORIGINS` - list of trusted origins for CSRF protection

For example:
```python
SECRET_KEY = 'n7+3u12_59wy_kzvecb^w^jrpi(m#(gl8^qe92kvclkd9!=-h)'
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
	"http://127.0.0.1:3000",
	"http://localhost:3000"
]
```
After saving the file, you can run all the containers with:
```bash
docker compose up --build	
  ```
  

## docker-compose.yml

The `docker-compose.yml` file provides an example Docker Compose configuration, which references the local `Dockerfile`

to build the required Docker images. You might need to modify it to fit your deployment.

  

## Creating a superuser

After starting all Docker containers, the command below can be used to create a superuser account.

`gutenberg-backend` is the name of the container running the Django server.

```bash

docker  exec  -it  gutenberg-backend  ./manage.py  createsuperuser

```
