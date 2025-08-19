import tailwindcss from "@tailwindcss/vite";
import Aura from "@primeuix/themes/aura";
import type { NuxtPage } from '@nuxt/schema';

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
          darkModeSelector: 'none',
        },
      },
    },
  },
  ssr: false,
  nitro: {
    preset: 'static',
    prerender: {
      crawlLinks: false,
      routes: ['/login'],
    },
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
      '/oidc/**': {
        proxy: {
          to: `${devDjangoUrl}oidc/**`,
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
  router: {
    options: {
      // See the comment for the `pages:extend` hook for the explanation
      strict: true,
    }
  },
  hooks: {
    // This hook, together with `router.options.strict` set to `true`,
    // make sure all router pages end with a trailing slash.
    //
    // This makes sure the routing is consistent with Django, which
    // automatically adds trailing slashes to routes using an HTTP redirect.
    'pages:extend'(pages) {
      const updatePathsRecursive = (pages: NuxtPage[]) => {
        pages.forEach(page => {
          if (!page.path.endsWith('/')) {
            page.path += '/';
          }
          updatePathsRecursive(page.children ?? [])
        });
      };
      updatePathsRecursive(pages);
    },
  },
  app: {
    cdnURL: '/static/'
  },
});
