import tailwindcss from "@tailwindcss/vite";
import Aura from "@primeuix/themes/aura";

const isDev = process.env.NODE_ENV === 'development';
let devDjangoUrl = process.env['GUTENBERG_DEV_DJANGO_URL'] || 'http://localhost:11111/';
if (!devDjangoUrl.endsWith('/')) devDjangoUrl += '/';

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/eslint', '@primevue/nuxt-module'],
  css: ['~/assets/css/main.css'],
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
  primevue: {
    options: {
      theme: {
        preset: Aura,
        options: {
          cssLayer: {
            name: 'primevue',
            order: 'theme, base, primevue',
          },
        },
      },
    },
  },
  ssr: false,
  nitro: {
    preset: 'static',
    routeRules: isDev ? {
      '/api-auth/**': {
        proxy: {
          to: `${devDjangoUrl}api-auth/**`,
        },
      },
      '/api/**': {
        proxy: {
          to: `${devDjangoUrl}api/**`,
        },
      },
      '/static/**': {
        proxy: {
          to: `${devDjangoUrl}static/**`,
        },
      },
      '/admin/**': {
        proxy: {
          to: `${devDjangoUrl}admin/**`,
        },
      },
    } : {},
  },
  app: {
    cdnURL: '/static/'
  },
});
