<template>
  <a
    :href="href"
    class="flex flex-row p-4 gap-4 items-center border rounded-border border-surface bg-surface-50 hover:bg-surface-0 transition-colors focus-ring"
  >
    <img
      v-if="imgSrc"
      :src="imgSrc"
      :alt="imgAlt"
      class="w-10 h-auto shrink-0"
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
