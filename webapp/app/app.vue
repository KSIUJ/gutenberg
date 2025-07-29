<template>
  <div>
    <NuxtLoadingIndicator />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
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
