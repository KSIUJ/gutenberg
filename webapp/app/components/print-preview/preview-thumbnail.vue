<template>
  <button
    type="button"
    class="focus-ring relative shrink-0 snap-start overflow-hidden rounded-xs border-2 bg-white"
    :class="selected ? 'border-primary' : 'border-surface hover:border-surface-300'"
    :style="{ width: '3.25rem', aspectRatio: `${page.width} / ${page.height}` }"
    :aria-label="`Page ${page.number}${side ? ` (${side})` : ''}`"
    :aria-current="selected"
    @click="$emit('click')"
  >
    <!-- There is no thumbnail endpoint, so this just shows the full-size image small. -->
    <img
      :src="page.image"
      :alt="''"
      class="size-full object-contain"
      loading="lazy"
      :style="{ imageOrientation: 'from-image', transform: rotated ? 'rotate(180deg)' : undefined }"
    >

    <span
      class="absolute inset-x-0 bottom-0 bg-black/55 text-center text-[0.6rem] leading-tight text-white"
    >{{ page.number }}</span>

    <!-- Front/back badge, shown for duplex and booklet pairs. -->
    <span
      v-if="side !== null"
      class="absolute right-0 top-0 rounded-bl-xs bg-primary px-1 text-[0.55rem] font-semibold leading-tight text-primary-contrast"
    >{{ side === 'front' ? 'F' : 'B' }}</span>
  </button>
</template>

<script setup lang="ts">
defineProps<{
  page: PrintPreviewPage;
  side: 'front' | 'back' | null;
  selected: boolean;
  rotated?: boolean;
}>();
defineEmits<{ click: [] }>();
</script>
