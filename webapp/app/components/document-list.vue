<template>
  <div>
    <div
      v-for="document in documents"
      :key="document.localId"
      class="py-2 flex flex-row"
    >
      <div class="grow shrink w-0">
        <div class="overflow-hidden whitespace-nowrap text-ellipsis">
          {{ document.filename }}
        </div>
        <div :class="formattedState(document.state).color">
          {{ formattedState(document.state).label }}
        </div>
      </div>
      <Button variant="text" label="Remove" severity="danger" @click="document.remove()" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type {JobDocument} from "~/composables/use-job-creator";

defineProps<{
  documents: readonly JobDocument[];
}>();

const formattedState = (state: JobDocument['state']) => {
  if (state === 'error') return {
    label: 'Upload failed',
    color: 'text-red-500',
  };
  return {
    label: {
      pending: 'Pending',
      uploading: 'Uploading…',
      uploaded: 'Uploaded',
    }[state],
    color: 'text-neutral-400',
  }
};
</script>
