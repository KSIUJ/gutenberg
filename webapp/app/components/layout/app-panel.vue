<template>
  <div :class="rootClass">
    <div
      v-if="header"
      class="px-7 sm:px-5 pt-5"
    >
      <h1>{{ header }}</h1>
    </div>
    <div class="px-7 sm:px-5 py-5 shrink grow overflow-y-auto flex flex-col">
      <slot />
    </div>
    <div
      v-if="$slots.actions"
      class="px-7 sm:px-5 pb-5 flex flex-row-reverse gap-2 shrink-0"
    >
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    header?: string;
    ghost?: boolean;
  }>(),
  {
    header: undefined,
    ghost: false,
  },
);

const rootClass = computed(() => {
  const commonClasses = 'border-y border-surface sm:rounded-border sm:border-x flex flex-col';
  if (props.ghost) {
    return `${commonClasses} border-dashed bg-surface-50`;
  }
  return `${commonClasses} bg-surface-0`;
});
</script>
