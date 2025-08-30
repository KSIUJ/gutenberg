<template>
  <div :class="rootClass">
    <div
      v-if="header"
      class="group shrink-0 border-b border-surface p-2 transition-colors"
      :class="{
        'cursor-pointer outline-none select-none hover:bg-primary-50': headerClickable,
      }"
      :tabindex="headerClickable ? 0 : undefined"
      :role="headerClickable ? 'button' : undefined"
      @click="onHeaderClick"
      @keydown.enter.prevent="onHeaderClick"
      @keyup.space.prevent="onHeaderClick"
    >
      <h1 class="rounded-xs px-3 py-1 text-header outline-offset-4 outline-primary group-focus-visible:outline">
        {{ header }}
      </h1>
    </div>
    <div class="flex shrink grow flex-col overflow-y-auto px-5 py-5">
      <slot />
    </div>
    <div
      v-if="$slots.actions"
      class="flex shrink-0 flex-row-reverse gap-2 px-5 pb-5"
    >
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    header?: string;
    headerClickable?: boolean;
    ghost?: boolean;
  }>(),
  {
    header: undefined,
    headerClickable: false,
    ghost: false,
  },
);

const emit = defineEmits<{
  headerClick: [event: MouseEvent];
}>();

const rootClass = computed(() => {
  const commonClasses = 'border-y border-surface sm:rounded-border sm:border-x flex flex-col overflow-hidden';
  if (props.ghost) {
    return `${commonClasses} border-dashed bg-surface-50`;
  }
  return `${commonClasses} bg-surface-0`;
});

const onHeaderClick = (event: MouseEvent) => {
  emit('headerClick', event);
};
</script>
