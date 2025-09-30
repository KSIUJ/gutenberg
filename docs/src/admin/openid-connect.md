# OpenID Connect

Gutenberg supports Single Sign-On with OpenID Connect
using an OpenID Connect client library developed at KSI:
<https://github.com/KSIUJ/ksi-oidc-python>.

Check out the [README of ksi-oidc-django] for more information.

The library was tested with Keycloak, other OpenID Connect providers should work as well,
but the role sync features might not work.

## Configuration steps

To configure OpenID Connect within Gutenberg, you need to:

### Django settings
1. Set the value of `OIDC_APP_BASE_URL` in the appropriate settings file
    (likely `local_setting.py`, `production_settings.py` or `docker_settings.py`)
    to the public URL of your Gutenberg instance.
    This URL will be used by the OpenID Connect provider to communicate with Gutenberg's auth
    backend and to redirect users to after authentication.

2. Set the values of `OIDC_SYNC_ROLES_AS_GROUPS`, `OIDC_STAFF_ROLE` and `OIDC_SUPERUSER_ROLE`.

    The recommended way to do this is to enable `OIDC_SYNC_ROLES_AS_GROUPS` - the group
    synchronization will be useful for specifying printing permissions.

    For `OIDC_STAFF_ROLE` and `OIDC_SUPERUSER_ROLE`, the default configuration is:
    ```
    OIDC_STAFF_ROLE = ('client', 'gutenberg-staff')
    OIDC_SUPERUSER_ROLE = ('client', 'gutenberg-superuser')
    ```
    This will let the users with the [Keycloak client role] `gutenberg-staff` access the admin panel
    and with the role `gutenberg-superuser` get all Django permissions.

3. Add `kdi_oidc_django.backends.OidcAuthBackend` to `AUTHENTICATION_BACKENDS`.
    This will enable signing in with OpenID Connect and replace the default login view
    with a redirect to the OpenID Connect provider.

### Creating a client in the OpenID Connect provider
[ksi-oidc-django] supports [OpenID Connect Dynamic Client Registration],
so only minimal configuration in the OpenID Provider is needed.

#### Dynamic client registration (also for existing clients)
To use it, first run the command:
```bash
uv run manage.py oidc_set_issuer
```
It will display a prompt for the issuer URI. When using Keycloak, the issuer URI is
`https://<keycloak-host>/realms/<realm-name>`.

The `oidc_set_issuer` command will verify that the provided URL is correct and accessible.

If your OpenID Connect Provider supports dynamic registration, use the `oidc_init_dynamic`
command to create the client:
```bash
uv run manage.py oidc_init_dynamic
```
This command can be used both for new and existing clients.
When creating a new client with Keycloak, you need to create an *Initial access
token* in the client list of the appropriate realm.

The command will use this token to register a new client with the redirect URIs,
name, logo and other setting configured for your deployment.

After updating Gutenberg or changing its Django settings, run the command below
to update the client configuration in the OpenID Connect Provider.
You should also run this command after configuring dynamic registration for an
existing client.
```bash
uv run manage.py oidc_update_config
```

The issuer URI, Client ID, Client Secret, registration access token and
configuration URI are stored in the default database configured in Django.
You can see and verify the stored setting using the command:
```
uv run manage.py oidc_info
```

#### Static client configuration
If you are unable to use dynamic client registration, [ksi-oidc-django] also
allows to set the Client ID and Client Secret manually.
Use the `oidc_init_static` command for this:
```
uv run manage.py oidc_init_static
```

You need to specify the *Valid redirect URIs* and *Valid post logout redirect URIs*
settings manually. Assuming `https://myapp.com/` is the public URL of your Gutenberg
instance (the value of the `OIDC_APP_BASE_URL` setting):
- Add `https://myapp.com/oidc/callback/` to *Valid redirect URIs*.
- Add `https://myapp.com/` to *Valid post logout redirect URIs*.

### Creating client roles
If you've configured role sync like described above in the [Django settings](#django-settings)
section, you should also create the `gutenberg-staff` and `gutenberg-superuser` client roles
in the Keycloak settings for your client.

If you have an admin realm role in your Keycloak realm, you can add the `gutenberg-staff`
and `gutenberg-superuser` roles in the *Associated roles* section of the realm role settings,
so that all admins automatically inherit these roles.


[ksi-oidc-django]: https://github.com/KSIUJ/ksi-oidc-python/blob/main/django/README.md
[README of ksi-oidc-django]: https://github.com/KSIUJ/ksi-oidc-python/blob/main/django/README.md
[Keycloak client role]: https://www.keycloak.org/docs/latest/server_admin/index.html#con-client-roles_server_administration_guide
[OpenID Connect Dynamic Client Registration]: https://openid.net/specs/openid-connect-registration-1_0.html
