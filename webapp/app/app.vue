<template>
  <div>
    <NuxtLoadingIndicator />
    <p-toast position="bottom-right" />
    <p-confirm-dialog />

    <app-header />
    <div class="mt-(--header-height)">
      <NuxtPage />
    </div>
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
    class: 'bg-surface-100 text-color',
  },
});
</script>
