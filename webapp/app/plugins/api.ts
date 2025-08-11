// This file is based on https://nuxt.com/docs/4.x/guide/recipes/custom-usefetch

export default defineNuxtPlugin((nuxtApp) => {
  const api = $fetch.create({
    baseURL: '/api/',
    async onResponseError({ response }) {
      if (response.status === 401) {
        alert('Login is required');
        // await nuxtApp.runWithContext(() => navigateTo('/login'))
      }
    },
  });

  // Expose to useNuxtApp().$api
  return {
    provide: {
      api,
    },
  };
});
