<template>
  <div class="flex max-w-xs flex-col items-center gap-3 text-center">
    <svg
      v-if="variant === 'loading'"
      viewBox="0 0 24 24"
      fill="none"
      class="size-8 animate-spin text-primary"
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-opacity="0.25"
      />
      <path
        d="M21 12a9 9 0 0 0-9-9"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
      />
    </svg>
    <svg
      v-else
      viewBox="0 0 24 24"
      fill="none"
      class="size-8 text-error"
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        stroke-width="2"
      />
      <path
        d="M12 7v6M12 16.5v.01"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
      />
    </svg>
    <p
      class="text-sm"
      :class="variant === 'error' ? 'text-error' : 'text-muted-color'"
    >
      <slot />
    </p>
    <slot name="action" />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ variant?: 'loading' | 'error' }>(), { variant: 'loading' });
</script>
