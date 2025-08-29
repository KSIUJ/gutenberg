<template>
  <!--
    The sign in button is not a NuxtLink, because the /login/ route might be handled by Django,
    not Vue Router, if OIDC sign-in is enabled.
  -->
  <p-button
    label="Sign in"
    as="a"
    href="/login/"
    :size="size"
    :variant="variant"
  />
</template>

<script lang="ts" setup>
import type { ButtonProps } from 'primevue';

defineProps<{
  size?: ButtonProps['size'];
  variant?: ButtonProps['variant'];
}>();
</script>
