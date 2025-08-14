<template>
  <div>
    <app-header />
    <NuxtLoadingIndicator />
    <NuxtPage />
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
    class: 'bg-background text-foreground',
  },
});
</script>
