<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6 py-4 sm:px-4 md:flex-row md:py-0">
    <!--
      This trickery with sticky makes it so that:
      - if the height of the left column is less than the screen height (minus the header height)
        the left panel is fixed (not affected by scrolling),
      - if it is greater then the left column will scroll with the page until its end touches
        the bottom edge of the screen.
      This way the left column is always in view, but if it doesn't fit on the screen global
      scroll is used to avoid nested scrolling.

      The sticky positioning is disabled when either:
       1. the layout is single-column,
       2. the device height is less than "y-md".
    -->
    <div class="w-full md:w-sm md:shrink-0 lg:w-md y-md:md:sticky y-md:md:bottom-0 y-md:md:self-end">
      <div class="flex flex-col md:py-4 y-md:md:sticky y-md:md:top-(--header-height) y-md:md:min-h-[calc(100vh-var(--header-height))]">
        <slot name="sidebar" />
      </div>
    </div>

    <div class="md:grow md:py-4">
      <slot name="content" />
    </div>
  </div>
</template>
