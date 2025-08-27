<template>
  <div>
    <p-toast position="bottom-right" />
    <app-header />
    <NuxtLoadingIndicator />
    <div class="mt-(--header-height)">
      <NuxtPage />
    </div>
  </div>
</template>

<script setup lang="ts">
import AppHeader from "~/components/app-header.vue";

useHead({
  title: 'Gutenberg',
  meta: [
    { name: 'description', content: 'The Gutenberg printing services' },
  ],
  htmlAttrs: {
    lang: 'en',
  },
  bodyAttrs: {
    class: 'bg-surface-100 text-color',
  },
});
</script>
