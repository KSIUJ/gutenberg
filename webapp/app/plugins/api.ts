// This file is based on https://nuxt.com/docs/4.x/guide/recipes/custom-usefetch

export default defineNuxtPlugin({
  name: 'api-plugin',

  setup: () => {
    const nuxtApp = useNuxtApp();
    const csrfToken = useCookie('csrftoken', { readonly: true });
    const toast = useToast();

    const api = $fetch.create({
      baseURL: '/api/',
      // Avoid leaking the X-CSRFToken, recommended by the Django docs (see the link below).
      mode: 'same-origin',
      credentials: 'same-origin',
      gutenbergExpectJson: true,
      gutenbergDisableUnauthenticatedHandling: false,

      onRequest(request) {
        // https://docs.djangoproject.com/en/5.2/howto/csrf/#using-csrf-protection-with-ajax

        // Make sure the CSRF token is up to date before sending the request
        refreshCookie('csrftoken');
        if (csrfToken.value) {
          request.options.headers.append('X-CSRFToken', csrfToken.value);
        }
        if (request.options.gutenbergExpectJson === true) {
          request.options.headers.set('accept', 'application/json');
        }
      },

      onResponse({ options, response }) {
        // An API response might update the CSRF token, make sure
        // the value of the `csrfToken` ref is up to date.
        refreshCookie('csrftoken');

        if (!response.ok || options.gutenbergExpectJson !== true) return;
        if (response.status === 204) {
          console.error(
            `Unexpected empty response from a request to "${response.url}. gutenbergExpectJson was set to true.`,
          );
          throw createError({
            message: 'Empty response received from the server',
            statusCode: 500,
          });
        }
        if (response.headers.get('content-type') !== 'application/json') {
          console.error(
            `Unexpected content type in a response from a request to "${response.url}".
            Expected "application/json", because gutenbergExpectJson was set to true, got: ${response.headers.get('content-type')}.`,
          );
          throw createError({
            message: 'Unexpected content type in a response from the server',
            statusCode: 500,
          });
        }
      },

      async onResponseError({ options, response }) {
        if (options.gutenbergDisableUnauthenticatedHandling) return;

        // Currently, unauthenticated requests return the 403 Forbidden status code,
        // not 401 Unauthorized. See:
        // https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication
        const isAuthError = response.status === 401 || response.status === 403;
        if (!isAuthError) return;
        // To distinguish between unauthenticated requests and missing permissions,
        // Gutenberg sets a custom X-Reason header for error responses.
        const reason = response.headers.get('X-Reason');
        if (reason !== 'NotAuthenticated' && reason !== 'AuthenticationFailed') return;

        if (!('$auth' in nuxtApp)) {
          console.warn('The auth plugin was not available in API plugin\'s onResponseError handler');
          return;
        }

        if (nuxtApp.$auth.me.value === Unauthenticated) {
          console.warn(`Got ${reason} auth error in API plugin's onResponseError handler, `
            + 'but `$auth.me` was already `Unauthenticated`');
          return;
        }

        try {
          await navigateTo(
            {
              path: '/login/',
              query: { next: useRoute().fullPath, expired: 'true' },
            },
            { external: true },
          );

          // Keep the request in the processing state while navigating to the login page.
          // The external navigation should cause a page load/reload, so this promise should
          // never complete, unless the login page load fails or actually takes very long.
          await new Promise(resolve => setTimeout(resolve, 5000));
          console.error('Page was still active 5s after starting navigation to the sign in page');
        } catch (error) {
          console.error('Failed to navigate to the sign in page after the session has expired', error);
        } finally {
          nuxtApp.$auth.clearMe();
          toast.add({
            summary: 'Your session has expired',
            detail: `Sign in again to continue`,
            severity: 'error',
          });
        }
      },
    });

    // Expose to useNuxtApp().$api and useNuxtApp().$csrfToken
    return {
      provide: {
        api,
        csrfToken,
      },
    };
  },
});
