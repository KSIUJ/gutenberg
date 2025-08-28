import tailwindcss from '@tailwindcss/vite';
import Aura from '@primeuix/themes/aura';
import type { NuxtPage } from '@nuxt/schema';

const isDev = process.env.NODE_ENV === 'development';
let devDjangoUrl = process.env['GUTENBERG_DEV_DJANGO_URL'] || 'http://localhost:11111/';
if (!devDjangoUrl.endsWith('/')) devDjangoUrl += '/';

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: ['@nuxt/eslint', '@primevue/nuxt-module'],
  ssr: false,
  components: [
    {
      path: '~/components',
      pathPrefix: false,
    },
  ],
  devtools: { enabled: true },
  app: {
    cdnURL: '/static/',
  },
  css: ['~/assets/css/main.css'],
  router: {
    options: {
      // See the comment for the `pages:extend` hook for the explanation
      strict: true,
    },
  },
  compatibilityDate: '2025-07-15',
  nitro: {
    preset: 'static',
    prerender: {
      crawlLinks: false,
      routes: [],
    },
    routeRules: isDev
      ? {
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
        }
      : {},
  },
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
  hooks: {
    // This hook, together with `router.options.strict` set to `true`,
    // make sure all router pages end with a trailing slash.
    //
    // This makes sure the routing is consistent with Django, which
    // automatically adds trailing slashes to routes using an HTTP redirect.
    'pages:extend'(pages) {
      const updatePathsRecursive = (pages: NuxtPage[]) => {
        pages.forEach((page) => {
          if (!page.path.endsWith('/')) {
            page.path += '/';
          }
          updatePathsRecursive(page.children ?? []);
        });
      };
      updatePathsRecursive(pages);
    },
  },
  eslint: {
    config: {
      stylistic: {
        semi: true,
        braceStyle: '1tbs',
      },
    },
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
    // The PrimeVue Nuxt module includes the styles of all PrimeVue components by default, and the
    // tree-shaking does not work correctly, see:
    // - https://github.com/primefaces/primevue/issues/7774
    // - https://github.com/primefaces/primevue/issues/7959
    // Until these issues are fixed upstream, manual imports are used.
    autoImport: false,
    components: {
      prefix: 'p',
      include: [
        'Button',
        'Divider',
        'Fieldset',
        'FileUpload',
        'FloatLabel',
        'InputNumber',
        'InputText',
        'Menu',
        'Message',
        'Panel',
        'Password',
        'Select',
        'SelectButton',
        'Step',
        'StepItem',
        'StepPanel',
        'Stepper',
        'Toast',
        'ToggleSwitch',
      ],
    },
  },
});
