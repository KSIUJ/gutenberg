<template>
  <div class="flex flex-row gap-4 w-full max-w-5xl px-4 mx-auto">
    <!--
      This trickery with sticky makes it so that:
      - if the height of the left column is less than the screen height (minus the header height)
        the left panel is fixed (not affected by scrolling),
      - if it is greater then the left column will scroll with the page until its end touches
        the bottom edge of the screen.
      This way the left column is always in view, but if it doesn't fit on the screen global
      scroll is used to avoid nested scrolling.
    -->
    <div class="w-md self-end sticky bottom-0">
      <div class="sticky top-(--header-height) min-h-[calc(100vh-var(--header-height))] py-4 space-y-4">
        <Panel
          header="Print files online"
          :pt="{
            root: 'flex flex-col',
            // contentContainer: 'grow h-0',
            content: 'h-full overflow-y-auto',
          }"
        >
          <print-options />
        </Panel>

        <Panel header="Recently printed">
          <div class="text-muted-color text-center p-6">This feature is not yet implemented</div>
        </Panel>
      </div>
    </div>
    <div class="py-4 grow">
      <h1>Other ways to print</h1>
      <h2>IPP</h2>
      <p v-for="i in 10" :key="i" class="h-50">
        Content paragraph 1
      </p>
    </div>
  </div>
</template>
<script setup lang="ts">
</script>
