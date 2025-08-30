<template>
  <div :class="rootClass">
    <slot />
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    narrow?: boolean;
  }>(),
  {
    narrow: false,
  },
);

const rootClass = computed(() => {
  const commonClasses = 'w-full py-4 sm:px-4 mx-auto';
  if (props.narrow) {
    return `${commonClasses} sm:max-w-md`;
  }
  return `${commonClasses} sm:max-w-5xl`;
});
</script>
