<template>
  <div :class="rootClass">
    <div
      v-if="header"
      class="p-2 border-b border-surface shrink-0 group"
      :class="{
        'cursor-pointer hover:bg-primary-50 outline-none select-none': headerClickable,
      }"
      :tabindex="headerClickable ? 0 : undefined"
      :role="headerClickable ? 'button' : undefined"
      @click="onHeaderClick"
      @keydown.enter.prevent="onHeaderClick"
      @keyup.space.prevent="onHeaderClick"
    >
      <h1 class="px-3 py-1 text-header rounded-xs outline-primary outline-offset-4 group-focus-visible:outline">
        {{ header }}
      </h1>
    </div>
    <div class="px-5 py-5 shrink grow overflow-y-auto flex flex-col">
      <slot />
    </div>
    <div
      v-if="$slots.actions"
      class="px-5 pb-5 flex flex-row-reverse gap-2 shrink-0"
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
