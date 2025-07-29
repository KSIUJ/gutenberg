<template>
  <div class="m-4 flex flex-row gap-4 w-full max-w-5xl mx-auto">
    <Panel header="Print now" class="w-md">
      <print-options />
    </Panel>
    <div class="grow">
      <h1>Other ways to print</h1>
      <h2>IPP</h2>
      <p>Content paragraph 1</p>
      <p>Content paragraph 2</p>
      <p>Content paragraph 3</p>
      <p>Content paragraph 4</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import Panel from 'primevue/panel';
</script>
