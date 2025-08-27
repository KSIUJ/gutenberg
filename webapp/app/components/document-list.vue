<template>
  <ul>
    <li
      v-for="document in documents"
      :key="document.localId"
      class="pl-1 py-2 flex flex-row space-x-2 group"
    >
      <div class="grow shrink w-0">
        <div class="overflow-hidden whitespace-nowrap text-ellipsis text-sm">
          {{ document.filename }}
        </div>
        <div
          :class="[
            formattedState(document.state).color,
            'text-xs',
          ]"
        >
          {{ formattedState(document.state).label }}
        </div>
      </div>
      <!-- FIXME: Hiding until hovered does not work with touch input -->
      <p-button
        class="hide-unless-group-hovered"
        variant="text"
        label="Remove"
        severity="danger"
        size="small"
        @click="document.remove()"
      />
    </li>
  </ul>
</template>

<script setup lang="ts">
import type {JobDocument} from "~/composables/use-job-creator";

defineProps<{
  documents: readonly JobDocument[];
}>();

const formattedState = (state: JobDocument['state']) => {
  if (state === 'error') return {
    label: 'Upload failed',
    color: 'text-error',
  };
  return {
    label: {
      pending: 'Pending',
      uploading: 'Uploading…',
      uploaded: 'Uploaded',
    }[state],
    color: 'text-muted-color',
  }
};
</script>
