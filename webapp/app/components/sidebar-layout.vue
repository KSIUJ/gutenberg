<template>
  <div class="flex flex-col md:flex-row gap-6 w-full max-w-5xl sm:px-4 py-4 md:py-0 mx-auto">
    <!--
      This trickery with sticky makes it so that:
      - if the height of the left column is less than the screen height (minus the header height)
        the left panel is fixed (not affected by scrolling),
      - if it is greater then the left column will scroll with the page until its end touches
        the bottom edge of the screen.
      This way the left column is always in view, but if it doesn't fit on the screen global
      scroll is used to avoid nested scrolling.
    -->
    <div class="w-full md:w-sm lg:w-md md:shrink-0 md:self-end md:sticky md:bottom-0">
      <div class="md:sticky md:top-(--header-height) md:min-h-[calc(100vh-var(--header-height))] md:py-4 flex flex-col">
        <slot name="sidebar" />
      </div>
    </div>

    <div class="md:py-4 md:grow">
      <slot name="content" />
    </div>
  </div>
</template>
<script setup lang="ts">
</script>
