<template>
  <div class="grid grid-cols-[var(--container-md)_1fr] gap-4 w-full max-w-5xl px-4 mx-auto">
    <div class="col-1 py-4">
      <div class="w-md fixed top-[calc(var(--spacing)*4+var(--header-height))] bottom-4">
        <Panel
          header="Print files online"
          class="h-full"
          :pt="{
            root: 'flex flex-col',
            contentContainer: 'grow',
            content: 'h-full',
          }"
        >
          <print-options />
        </Panel>
      </div>
    </div>
    <div class="col-2 py-4">
      <h1>Other ways to print</h1>
      <h2>IPP</h2>
      <p v-for="i in 5" :key="i" class="h-50">
        Content paragraph 1
      </p>
    </div>
  </div>
</template>
