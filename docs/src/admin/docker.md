# Deploying a Gutenberg instance with Docker
The Gutenberg project provides a Docker configuration to simplify the deployment on your server.

## Dockerfile modifications
We intend to publish container images based on the `Dockerfile` in the future. If your use-case requires modifications
to the `Dockerfile` we encourage you to create an issue in the Gutenberg's
[GitHub issue tracker](https://github.com/KSIUJ/gutenberg/issues/). This way we can ensure that the published images
are suitable for customized setups.

## Required images
Gutenberg requires configuring a PostgreSQL database, a Redis instance, and a CUPS server.
All of them need to be accessible from the Django server and from the Celery worker.
They can be deployed as Docker containers or as standalone instances.
On top of that, three more containers are required to run Gutenberg:
the Django backend server, the Celery worker for executing background tasks, and the Nginx proxy that routes incoming HTTP requests and serves static files.

In summary:

| Container name       | Description                                      |
|:-------------------- |:------------------------------------------------ |
| `gutenberg-db`       | PostgreSQL database for storing application data |
| `gutenberg-redis`    | Redis instance for caching and task queue        |
| `gutenberg-backend`  | Django application server                        |
| `gutenberg-celery`   | Celery worker for background tasks               |
| `gutenberg-proxy`    | Nginx for routing requests                       |

## Configuration
To run Gutenberg in Docker, you need to create your own version of the settings:
```bash
  cp backend/gutenberg/settings/docker_settings.py.example backend/gutenberg/settings/docker_settings.py
```
In `docker_settings.py`, fill in the following fields properly:
* `SECRET_KEY` - unique random string 
* `ALLOWED_HOSTS` - list of hosts that can connect to the app
* `CSRF_TRUSTED_ORIGINS` - list of trusted origins for CSRF protection

For example:
```python
SECRET_KEY = 'n7+3u12_59wy_kzvecb^w^jrpi(m#(gl8^qe92kvclkd9!=-h)'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:3000',
    'http://localhost:3000',
]
```
After saving the file, you can run all the containers with:
```bash
docker compose up --build	
```

## docker-compose.yml
The `docker-compose.yml` file provides an example Docker Compose configuration, which references the local `Dockerfile`
to build the required Docker images. You might need to modify it to fit your deployment.

Two secrets need to be provided for Docker Compose: `gutenberg_postgres_password` and
`gutenberg_django_secret_key`. They should be randomly generated strings and should be kept secret.
Please make sure to never commit them in a Git repository. The `openssl` command can be used
to generate the secrets:

```bash
# Create a secrets directory with a `.gitignore` file
mkdir -p secrets
printf "# Avoid publishing any secrets stored in this folder\n*\n" > secrets/.gitignore

# Generate the secrets
openssl rand -base64 32 > ./secrets/postgres_password.txt
openssl rand -base64 32 > ./secrets/django_secret_key.txt
```

## Creating a superuser account
After starting all Docker containers, the command below can be used to create a superuser account.
`gutenberg-backend` is the name of the container running the Django server.

```bash
docker exec -it gutenberg-backend ./manage.py createsuperuser
```

## NGINX config files
The `run_nginx` target describes an NGINX Docker image with configuration required for running Gutenberg itself.
The default configuration file for NGINX, `/etc/nginx/nginx.conf` contains
an [include](https://nginx.org/en/docs/ngx_core_module.html#include) directive:
```conf
http {
    # ...
    include /etc/nginx/conf.d/*.conf```
    #...
}
```
Gutenberg adds a single file in the `conf.d` directory: `/etc/nginx/conf.d/gutenberg.conf`.
It defines an HTTP server which contains another `include` directive:
```conf
server {
    # ...
    include /etc/nginx/gutenberg-locations.d/*.conf;
    # ...
}
```
The files in the `gutenberg-locations.d` define [`location`](https://nginx.org/en/docs/http/ngx_http_core_module.html#location)
directives for different endpoints which will be available under the Gutenberg domain.

Gutenberg adds a singe file to this folder, `gutenberg-app.conf` which define the handlers for the endpoints
`/static/`, `/@webapp-html/` for internal use and a catch-all `location /` directive which proxies all requests to
the Django application server.

### Extending the NGINX configuration
You can make use of the `include` directives described above to extend Gutenberg's default NGINX image with your own
config.

As an example, this is how you would add a custom `/myapp/` endpoint proxied to https://example.com/myapp/:

Create a new file `myapp.conf` with the contents:
```conf
location /myapp/ {
    proxy_pass https://example.com/myapp/;
}
```

And your own `Dockerfile` with:
```Dockerfile
# Put the name Gutenberg's default NGINX image here:
FROM run_nginx

COPY path/to/myapp.conf /etc/nginx/gutenberg-locations.d/myapp.conf
```

## Configuring CUPS access
The `CUPS_SERVERNAME` setting controls how Gutenberg connects to CUPS.
It can be a path to a CUPS socket file, an IP address, or a hostname.
It will be used as the `-f` argument to commands provided by `cups-client`
(`lp`, `cancel`, etc.).

To use the CUPS server running on the host machine, you can mount the
`/run/cups` directory from the host machine to the Docker containers for
the backend and the Celery worker. The example `docker-compose.yml` file
does this. The `CUPS_SERVERNAME` can then be set to `/run/cups/cups.sock`.

> [!WARNING]
> Docker Desktop might not allow mounting any files from the `/run` directory,
> even if it is listed in *Resources* > *File sharing* > *Virtual file shares*.
> Failing to bind the `/run/cups/cups.sock` socket will not result in an error,
> Docker will silently create a new directory in that path.
> 
> This issue might be hard to overcome when using Docker Desktop, so we recommend
> installing the Docker engine directly.

CUPS performs permission checking when accessing CUPS via the socket file.
It requires the name and UID of the system user calling the `lp` command
in the Docker container to match a user on the host machine.
The `run_backend` and `run_celery` targets in the `Dockerfile` use the
`GUTENBERG_USERNAME`, `GUTENBERG_UID`, and `GUTENBERG_GID` environment
variables to set the username, UID, and GID of the user in the Docker
container. If they are not specified, the default username
`gutenberg-docker` is used and the UID and GID are set to `659`.

The same group and user need to be created on the host machine.
This can be achieved using the commands:
```bash
sudo groupadd --system --gid 659 gutenberg-docker
sudo useradd --system --groups lp,lpadmin gutenberg-docker --uid 659 --gid 659
```

> [!TIP]
> If the Gutenberg user is not configured correctly, attempting to print
> a document might result in an error like:
> > lp: Unauthorized
>
> In such cases it can be helpful to inspect the host's CUPS server error
> logs:
> ```bash
> less +G /var/log/cups/error_log
> ```
