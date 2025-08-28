<template>
  <single-column-layout narrow>
    <app-panel>
      <p-message
        v-if="job.error.value !== undefined"
        severity="error"
      >
        {{ errorMessage }}
      </p-message>
      <template v-else-if="job.data.value !== undefined">
        {{ job.data.value.id }}
        {{ job.data.value.status }}
        {{ job.data.value.status_reason }}
      </template>
    </app-panel>
  </single-column-layout>
</template>

<script setup lang="ts">
const apiRepository = useApiRepository();
const route = useRoute();
const job = await useAsyncData(
  () => apiRepository.getJob(parseInt(route.params.jobId as string)),
  {
    watch: [() => route.params.jobId],
  },
);
watch(() => job.error.value, (error) => {
  if (error === undefined) return;
  console.error(error);
}, { immediate: true });
const errorMessage = computed(() => {
  if (job.error.value === undefined) return null;
  return getErrorMessage(job.error.value) ?? 'Failed to load print job details';
});

definePageMeta({
  validate: async (route) => {
    return typeof route.params.jobId === 'string' && /^\d+$/.test(route.params.jobId);
  },
  middleware: [
    'require-auth',
  ],
});
</script>
