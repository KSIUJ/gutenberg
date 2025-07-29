import PrimeVue from "primevue/config";
import Aura from "@primeuix/themes/aura";

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(PrimeVue, {
    theme: {
      preset: Aura,
      options: {
        cssLayer: {
          name: 'primevue',
          order: 'theme, base, primevue'
        }
      }
    },
  });
});
