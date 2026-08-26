<template>
  <img
    :key="page.number"
    :src="page.image"
    :alt="`Page ${page.number} of the print preview`"
    class="rounded-xs bg-white object-contain shadow-md"
    :style="{
      aspectRatio: `${page.width} / ${page.height}`,
      transform: rotated ? 'rotate(180deg)' : undefined,
      imageOrientation: 'from-image',
    }"
  >
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  page: PrintPreviewPage;
  rotated?: boolean;
}>(), { rotated: false });
</script>
