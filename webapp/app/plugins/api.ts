// This file is based on https://nuxt.com/docs/4.x/guide/recipes/custom-usefetch

export default defineNuxtPlugin((nuxtApp) => {
  const csrfToken = useCookie('csrftoken', { readonly: true });

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
    async onResponseError({ response }) {
      // Currently, unauthenticated requests return the 403 Forbidden status code,
      // not 401 Unauthorized. See:
      // https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication
      //
      // If automatic redirection to the login page is implemented,
      // it should verify if the user is actually not logged in,
      // or if they are logged in but do not have permission to access the requested resource.
      // A redirect should only happen in the former case,
      // otherwise the user might get stuck in a redirect loop.
      if (response.status === 401 || response.status === 403) {
        // TODO: If the user is actually not logged in,
        // reset me in useAuth()
        alert('Login is required');
        // await nuxtApp.runWithContext(() => navigateTo('/login'))
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
});
