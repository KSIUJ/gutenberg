<template>
  <div :class="rootClass">
    <slot />
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    warn?: boolean;
  }>(),
  {
    warn: false,
  },
);

const rootClass = computed(() => {
  const commonClasses = 'mt-1 text-xs';
  if (props.warn) {
    return `${commonClasses} text-warn`;
  }
  return `${commonClasses} text-muted-color`;
});
</script>
