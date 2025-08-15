// This file is based on https://nuxt.com/docs/4.x/guide/recipes/custom-usefetch

export default defineNuxtPlugin({
  name: 'api-plugin',

  setup: (nuxtApp) => {
    const csrfToken = useCookie('csrftoken', { readonly: true });
    // TODO: Remove this temporary solution
    const toast = useToast();

    const api = $fetch.create({
      baseURL: '/api/',
      // Avoid leaking the X-CSRFToken, recommended by the Django docs (see the link below).
      mode: 'same-origin',
      credentials: 'same-origin',

      onRequest(request) {
        // https://docs.djangoproject.com/en/5.2/howto/csrf/#using-csrf-protection-with-ajax

        // Make sure the CSRF token is up to date before sending the request
        refreshCookie('csrftoken');
        if (csrfToken.value) {
          request.options.headers.append('X-CSRFToken', csrfToken.value);
        }
      },

      onResponse() {
        // An API response might update the CSRF token, make sure
        // the value of the `csrfToken` ref is up to date.
        refreshCookie('csrftoken');
      },

      async onResponseError({response }) {
        // Currently, unauthenticated requests return the 403 Forbidden status code,
        // not 401 Unauthorized. See:
        // https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication
        //
        // To distinguish between unauthenticated requests and missing permissions,
        // Gutenberg sets a custom X-Reason header for error responses.

        const isAuthError = response.status === 401 || response.status === 403;
        if (isAuthError) {
          const reason = response.headers.get('X-Reason');
          if (reason === 'NotAuthenticated' || reason === 'AuthenticationFailed') {
            // TODO: Reset `me` in the auth plugin

            // TODO: Remove this temporary solution
            setTimeout(() => {
              toast.add({
                summary: 'The user is not authenticated',
                detail: `Got code ${response.status}: ${response.statusText},\n X-Reason: ${reason}`,
                severity: 'error',
                life: 3000,
              });
            }, 1000);

            // TODO: Decide on automatic redirects to the login page.
            //  This might lead to unexpected data loss or the desired action not actually getting
            //  executed after the user attempts an action resulting in the 401/403 error response.

            // await nuxtApp.runWithContext(() => navigateTo('/login'))
          }
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
