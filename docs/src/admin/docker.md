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
* `ALLOWED_HOSTS` - list of hosts that can connect to the app
* `CSRF_TRUSTED_ORIGINS` - list of trusted origins for CSRF protection

In addition, the value of `SECRET_KEY` will by default be read from the Docker secret
`gutenberg_django_secret_key`. It should be set to a unique random string.
An example of how to generate one can be found below in the [docker-compose.yml](#docker-composeyml) section.

For example:
```python
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

Gutenberg adds three files to this folder:
- `10-gutenberg-backend.conf` which defines a catch-all `location /` directive which proxies all requests to the Django backend.
- `15-gutenberg-static.conf` which defines the handlers for the endpoints:
  - `/static/` for serving static files.
  - `/@webapp-html/` for internal use with the `X-Accel-Redirect` header.
- `20-gutenberg-docs.conf` which defines the handlers for the `/docs/` endpoint
  which serves the mdbook documentation.

`10-gutenberg-backend.conf` is generated at runtime based on these environment variables:
- `GUTENBERG_TRUST_X_FORWARDED_HOST`
  - Possible values: `0` (default), `1`
- `GUTENBERG_TRUST_X_FORWARDED_PROTO`
  - Possible values: `0` (default), `1`
- `GUTENBERG_TRUST_X_REAL_IP`
  - Possible values: `0` (default), `1`

These settings determine how the `X-Forwarded-Host`, `X-Forwarded-Proto` and `X-Real-Ip`
headers are populated in the request to the `gutenberg-backend` container.
Only set these to `1` if all the following are true:
1. there is another proxy server before this NGINX container,
2. untrusted access is only possible via that proxy, and
3. the proxy securely populates these headers.

### Trusted Proxy Configuration

**What GUTENBERG_TRUSTED_PROXY_IPS does:**
Filters incoming requests by source IP address. Only requests from IP addresses within the configured ranges are allowed to reach the application; requests from other addresses receive HTTP 400.

**Why configure it:**
When Gutenberg runs behind a reverse proxy, the application needs to trust headers like `X-Forwarded-For`, `X-Forwarded-Host`, and `X-Real-IP` to determine the original client IP and the original value of the `Host` header. Without IP filtering, an attacker could send requests directly to the exposed nginx port with spoofed forwarded headers, bypassing [`ALLOWED_HOSTS`](https://docs.djangoproject.com/en/6.0/ref/settings/#allowed-hosts) or IP address checks. This setting ensures only your known proxy servers can send requests with these trusted headers.

**Default behavior:** By default, Gutenberg accepts all requests without IP filtering (`0.0.0.0/0`). This works for deployments without a reverse proxy or when proxy header trust is not enabled.

**When to configure:** If you enable any of the `GUTENBERG_TRUST_X_FORWARDED_*` options, you **must** also set `GUTENBERG_TRUSTED_PROXY_IPS` to specify which proxy IP addresses are trusted. Without this configuration, the container will fail to start as a security safeguard.

**How to configure:** Set both the trust flag and the IP ranges for the `proxy` service:

```yaml
proxy:
  environment:
    GUTENBERG_TRUST_X_FORWARDED_HOST: "1"
    GUTENBERG_TRUSTED_PROXY_IPS: "10.0.0.0/8 172.17.0.0/16"
```

**Format:** Space or comma-separated IP addresses and CIDR ranges (e.g., `"10.0.0.1 192.168.1.0/24"`).

**IPv6:** Include IPv6 ranges if needed (e.g., `"172.17.0.0/16 fc00::/7"`).

### SSL/TLS Configuration

**What SSL configuration does:**
Enables HTTPS support in the nginx proxy, allowing encrypted connections to Gutenberg. The nginx container can terminate SSL/TLS connections using certificates you provide via Docker volumes.

**Default behavior:** 
SSL is disabled by default. Gutenberg serves HTTP only on port 80, exactly as before this feature was added. Enabling SSL requires explicit configuration and providing SSL certificates.

**When to configure:** 
Configure SSL/TLS when you have obtained SSL certificates for your domain (e.g., from Let's Encrypt, your organization's certificate authority, or a commercial CA) and want the nginx container to handle SSL termination directly.

**How to configure:**

1. Obtain SSL certificates and place them in a directory accessible to Docker (e.g., `./ssl/`):
   ```bash
   # Example: Using Let's Encrypt with certbot
   sudo certbot certonly --standalone -d gutenberg.example.com
   # Certificates will be in /etc/letsencrypt/live/gutenberg.example.com/
   ```

2. Configure the proxy service with SSL settings in `docker-compose.yml`:

   ```yaml
   proxy:
     ports:
       - "80:80"    # HTTP (optional - for redirect or dual-mode)
       - "443:443"  # HTTPS
     volumes:
       - type: bind
         source: /etc/letsencrypt/live/gutenberg.example.com/fullchain.pem
         target: /etc/ssl/certs/gutenberg.crt
         read_only: true
       - type: bind
         source: /etc/letsencrypt/live/gutenberg.example.com/privkey.pem
         target: /etc/ssl/certs/gutenberg.key
         read_only: true
     environment:
       GUTENBERG_SSL_ENABLE: "1"
       GUTENBERG_SSL_CERT_PATH: "/etc/ssl/certs/gutenberg.crt"
       GUTENBERG_SSL_KEY_PATH: "/etc/ssl/certs/gutenberg.key"
       GUTENBERG_SSL_REDIRECT_HTTP: "1"
       GUTENBERG_SSL_HSTS_ENABLE: "1"
   ```

**Environment Variables:**

| Variable | Description | Default | Required when SSL enabled |
|----------|-------------|---------|---------------------------|
| `GUTENBERG_SSL_ENABLE` | Enable SSL support (set to `1`) | `0` (disabled) | Yes |
| `GUTENBERG_SSL_CERT_PATH` | Path to SSL certificate file inside container | None | Yes |
| `GUTENBERG_SSL_KEY_PATH` | Path to SSL private key file inside container | None | Yes |
| `GUTENBERG_SSL_PORT` | HTTPS port | `443` | No |
| `GUTENBERG_SSL_PROTOCOLS` | Space-separated SSL/TLS protocols | `TLSv1.2 TLSv1.3` | No |
| `GUTENBERG_SSL_CIPHERS` | SSL cipher suite (empty = nginx defaults) | Empty | No |
| `GUTENBERG_SSL_REDIRECT_HTTP` | Redirect HTTP to HTTPS (set to `1`) | `0` (dual-mode) | No |
| `GUTENBERG_SSL_HSTS_ENABLE` | Enable HSTS header (set to `1`) | `0` (disabled) | No |
| `GUTENBERG_SSL_HSTS_MAX_AGE` | HSTS max-age in seconds | `31536000` (1 year) | No |
| `GUTENBERG_SSL_HSTS_INCLUDE_SUBDOMAINS` | Include subdomains in HSTS (set to `1`) | `0` | No |
| `GUTENBERG_SSL_HSTS_PRELOAD` | Enable HSTS preload (set to `1`) | `0` | No |

**Certificate Formats:**

- `GUTENBERG_SSL_CERT_PATH` should point to the **full certificate chain** (often named `fullchain.pem` in Let's Encrypt)
- `GUTENBERG_SSL_KEY_PATH` should point to the **private key** (often named `privkey.pem`)
- Both files must be readable by the nginx process (certificate: 644 permissions, key: 600 permissions)

**HTTP Behavior with SSL:**

By default, when SSL is enabled (`GUTENBERG_SSL_ENABLE=1`), both HTTP (port 80) and HTTPS (port 443) serve the full application content (dual-mode). This allows gradual migration or mixed access scenarios.

To redirect all HTTP traffic to HTTPS, set `GUTENBERG_SSL_REDIRECT_HTTP=1`. In this mode:
- Requests to `http://gutenberg.example.com/` redirect to `https://gutenberg.example.com/`
- HTTP port 80 only serves the redirect (no content)

**HSTS Configuration:**

HTTP Strict Transport Security (HSTS) tells browsers to **only** access the site via HTTPS in the future. Enable it with `GUTENBERG_SSL_HSTS_ENABLE=1` only if:
- You're committed to serving the site over HTTPS permanently
- All subdomains (if `INCLUDE_SUBDOMAINS=1`) support HTTPS
- You understand that HSTS is cached by browsers (for `max-age` seconds)

> [!WARNING]
> **HSTS Preload** (`GUTENBERG_SSL_HSTS_PRELOAD=1`) submits your domain to browser vendors' HSTS preload lists. This is **permanent** and very difficult to undo. Only enable preload if you are certain you will never serve the domain over HTTP again.

**SSL Protocols and Ciphers:**

The default settings (`TLSv1.2 TLSv1.3` with nginx default ciphers) provide a secure, modern configuration suitable for most deployments. Only customize these if you have specific compliance requirements or need to support legacy clients.

**Certificate Renewal:**

SSL certificates expire and must be renewed periodically (Let's Encrypt certificates expire every 90 days).

To reload nginx after renewing certificates without restarting the container:
```bash
docker exec gutenberg-proxy nginx -s reload
```

For automated renewal with Let's Encrypt certbot, add a renewal hook:
```bash
# /etc/letsencrypt/renewal-hooks/deploy/reload-gutenberg.sh
#!/bin/bash
docker exec gutenberg-proxy nginx -s reload
```

**Troubleshooting:**

| Problem | Solution |
|---------|----------|
| Container fails to start with "certificate file not found" | Verify volume mount paths in `docker-compose.yml` match actual certificate locations on host |
| Container fails to start with "not readable" error | Check file permissions: `chmod 644` for certificate, `chmod 600` for key |
| Browser shows "certificate not trusted" error | Ensure you're using the **full chain** certificate (`fullchain.pem`), not just the certificate (`cert.pem`) |
| Browser shows "certificate name mismatch" | Certificate must be issued for the exact domain name you're accessing |
| HTTPS works but HTTP doesn't | Port 80 must be mapped in `docker-compose.yml`: `"80:80"` |
| HTTP doesn't redirect to HTTPS | Set `GUTENBERG_SSL_REDIRECT_HTTP=1` |

**Example: Self-Signed Certificate for Testing:**

For development/testing only, you can generate a self-signed certificate:

```bash
mkdir -p ./ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/privkey.pem \
  -out ./ssl/fullchain.pem \
  -subj "/CN=localhost"
```

Then use `source: ./ssl/fullchain.pem` and `source: ./ssl/privkey.pem` in the docker-compose volumes.

> [!WARNING]
> Self-signed certificates are **not suitable for production**. Browsers will show security warnings, and clients must explicitly trust the certificate.

**Migration Notes:**

If you previously customized the nginx configuration by modifying the `nginx/20-gutenberg.conf` file, note that this file has been removed. Server blocks are now generated dynamically by entrypoint scripts based on environment variables.

To customize nginx configuration:
- Place custom location blocks in `nginx/locations/` (see "Extending the NGINX configuration" below)
- Use environment variables for SSL, trusted proxies, and backend settings
- For advanced customization, create custom entrypoint scripts in `nginx/entrypoint/`

### Extending the NGINX configuration
You can make use of the `include` directives described above to extend Gutenberg's default NGINX image with your own
config.

As an example, this is how you would add a custom `/myapp/` endpoint proxied to https://example.com/myapp/:

Create a new file `30-myapp.conf` with the contents:
```conf
location /myapp/ {
    proxy_pass https://example.com/myapp/;
}
```

And your own `Dockerfile` with:
```Dockerfile
# Put the name Gutenberg's default NGINX image here:
FROM run_nginx

COPY path/to/30-myapp.conf /etc/nginx/gutenberg-locations.d/
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
