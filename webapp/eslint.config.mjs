// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs';
import tailwind from 'eslint-plugin-tailwindcss';
import { fileURLToPath } from 'url';

export default withNuxt([
  ...tailwind.configs['flat/recommended'],
  {
    settings: {
      tailwindcss: {
        config: fileURLToPath(import.meta.resolve('./app/assets/css/main.css')),
      },
    },
  },
]);
