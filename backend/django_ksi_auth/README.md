# django-ksi-auth

## Notice
The source code of this library incorporates modified source code from the [mozilla-django-oidc] library.
The fragments based on [mozilla-django-oidc] are appropriately marked in comments in the source code.
[mozilla-django-oidc] is licenced under the **Mozilla Public License 2.0**, available 
[here](https://github.com/mozilla/mozilla-django-oidc/blob/main/LICENSE).

[mozilla-django-oidc]: https://github.com/mozilla/mozilla-django-oidc

## Configuration
In the appropriate Django setting files:

1. Add `django.contrib.auth` (if not yet added) and `django_ksi_auth` to `INSTALLED_APPS`.

    It is required for adding the models for this library when running `manage.py migrate`
    and provides extra configuration checks.
    ```python
    INSTALLED_APPS = [
        # ...
        'django.contrib.auth',
        # ...
        'django_ksi_auth',
        # ...
    ]
    ```

2. Add the `KsiAuthMiddleware` to `MIDDLEWARE`:

    It must be placed __directly after__ Django's `AuthenticationMiddleware`, 
    because it is required for the session expiry and refresh logic to work.
    If any other middleware was added in between `AuthenticationMiddleware` and `KsiAuthMiddleware`,
    the `request.user` might be a user whose session has expired while processing that middleware.

    See [the Middleware Ordering section in the Django docs](https://docs.djangoproject.com/en/5.2/ref/middleware/#middleware-ordering)
    for a standard order of other middleware.
    ```python
    MIDDLEWARE = [
        # ...
        'django.contrib.sessions.middleware.SessionMiddleware',
        # ...
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django_ksi_auth.middleware.KsiAuthMiddleware',
        # ...
    ]
    ```

3. Add `django_ksi_auth`-specific settings:

    ```python
    KSI_AUTH_PROVIDER = {
       # For example https://auth.ksi.ii.uj.edu.pl/auth/realms/KSI
       # The auth plugin will reach https://auth.ksi.ii.uj.edu.pl/auth/realms/KSI/.well-known/openid-configuration
       # for configuration discovery
       'issuer': '######',

       # SECURITY: Do not check these secrets into version control!
       'client_id': '######',
       'client_secret': '######',
   
       # Set user's Django groups to the roles from the access token claims.
        # Note that this will also remove the user from the groups that are not present in the access token.
        'sync_roles_as_groups': False,

        # Sets or unsets the User.is_staff and User.is_superuser fields
        # if the access token contains claims for these roles.
        # Set to None to disable this feature.
        'staff_role': 'ksi-admin',
        'superuser_role': 'ksi-admin',
    }
    KSI_AUTH_SSO_CHECK_COOLDOWN_SECONDS = 300
    ```

4. Add `KsiAuthBackend` to `AUTHENTICATION_BACKENDS`:
    
    ```python
    AUTHENTICATION_BACKENDS = (
        # This is the standard Django backend, you can remove it if you only use
        # OpenID Connect for authentication.
        'django.contrib.auth.backends.ModelBackend',
        'django_ksi_auth.auth_backend.KsiAuthBackend',
    )
    ```
   
    You can disable the `KsiAuthBackend` without removing the app and middleware.
    The middleware will detect that the backend is not enabled and raise [`MiddlewareNotUsed`].

### Views configuration
Add these entries in your `urls.py`:
```python
urlpatterns = [
    # ...
    
    path('login/', BaseLoginView.as_view(), name='login'),
    
    # Register the endpoints `/oidc/callback/` and `/oidc/logout/`:
    path('oidc/', include('django_ksi_auth.urls')),
]
```
You may change the paths. Make sure to set the setting [`LOGIN_URL`] to the path of the login page.
`django-ksi-auth` also uses the standard [`LOGOUT_REDIRECT_URL`] setting, set it to the path
you want the user to be redirected to after logging out.

In the settings of your OIDC provider you will need to add the `/oidc/callback/` URL as a valid redirect URL
and the [`LOGOUT_REDIRECT_URL`] URL as a valid post logout redirect URL.

`BaseLoginView` redirects the user to the OIDC provider's login page if the `KsiAuthBackend` is enabled.
If it's not, it uses the view specified in `BaseLoginView.fallback_view` to render the login page.
It uses [`DjangoLoginView`] by default. You can use a different view for this by subclassing `BaseLoginView`
and overriding the `fallback_view` property.

```python
# in views.py:
class CustomLoginView(BaseLoginView):
    fallback_view = MyFallbackLoginView.as_view()

# in urls.py:
urlpatterns = [
    # ...
    path('login/', CustomLoginView.as_view(), name='login'),
    # ...
]
```

## Custom decorators
`django-ksi-auth` provides these new view decorators:

- `@ksi_auth_login_required` performs the same check as Django's `@login_required`,
    but if the user is not logged in, it redirects the user directly to the OIDC login page
    (if the `KsiAuthBackend` is enabled).
    
    If you were to use `@login_required` instead, accessing a protected view would redirect the user twice,
    first to the `LOGIN_URL`, which would then redirect the user to the OIDC login page.

- `@ksi_auth_check_sso` is used for views that do not require authentication.
    When an unauthenticated user tries to access a view decorated with `@ksi_auth_check_sso`,
    they will be redirected to the OIDC authentication endpoint with `prompt=none`,
    to check if the user already has an active SSO session.

    The `KSI_AUTH_SSO_CHECK_COOLDOWN_SECONDS` setting controls the minimum time between such checks.

[`LOGIN_URL`]: https://docs.djangoproject.com/en/5.2/ref/settings/#login-url
[`LOGOUT_REDIRECT_URL`]: https://docs.djangoproject.com/en/5.2/ref/settings/#logout-redirect-url
[`MiddlewareNotUsed`]: https://docs.djangoproject.com/en/5.2/topics/http/middleware/#marking-middleware-as-unused.
[`DjangoLoginView`]: https://docs.djangoproject.com/en/5.2/topics/auth/default/#django.contrib.auth.views.LoginView
