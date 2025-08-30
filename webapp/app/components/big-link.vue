<template>
  <a
    :href="href"
    class="flex flex-row items-center gap-4 rounded-border border border-surface bg-surface-50 p-4 focus-ring transition-colors hover:bg-surface-0"
  >
    <img
      v-if="imgSrc"
      :src="imgSrc"
      :alt="imgAlt"
      class="h-auto w-10 shrink-0"
    >

    <div
      class="grow text-center"
    >
      <slot>
        <b
          v-if="label"
          class="text-primary"
        >{{ label }}</b>
      </slot>
    </div>
  </a>
</template>

<script setup lang="ts">
defineProps<{
  href: string;
  imgSrc?: string;
  imgAlt?: string;
  label?: string;
}>();
</script>
