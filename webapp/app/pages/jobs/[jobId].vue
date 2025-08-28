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
        <p-button
          v-if="cancelable"
          severity="danger"
          label="Cancel"
          :loading="cancelLoading"
          @click="cancelJob"
        />
      </template>
    </app-panel>
  </single-column-layout>
</template>

<script setup lang="ts">
const apiRepository = useApiRepository();
const route = useRoute();
const toast = useToast();

const jobId = computed(() => parseInt(route.params.jobId as string));
const job = await useAsyncData(
  () => apiRepository.getJob(jobId.value),
  { watch: [jobId] },
);
watch(() => job.error.value, (error) => {
  if (error === undefined) return;
  console.error(error);
}, { immediate: true });

const errorMessage = computed(() => {
  if (job.error.value === undefined) return null;
  return getErrorMessage(job.error.value) ?? 'Failed to load print job details';
});

const COMPLETED_STATUSES: JobStatus[] = ['COMPLETED', 'ERROR', 'CANCELED', 'UNKNOWN'];
const cancelable = computed(() => {
  if (!job.data.value) return false;
  return !COMPLETED_STATUSES.includes(job.data.value.status);
});

const cancelLoading = ref(false);
const cancelJob = async () => {
  if (cancelLoading.value) return;
  try {
    cancelLoading.value = true;
    job.data.value = await apiRepository.cancelPrintJob(jobId.value);
  } catch (error) {
    console.error('Failed to cancel job', error);
    toast.add({
      summary: getErrorMessage(error) ?? 'Failed to cancel job',
      severity: 'error',
      life: 3000,
    });
  } finally {
    cancelLoading.value = false;
  }
};

definePageMeta({
  validate: async (route) => {
    return typeof route.params.jobId === 'string' && /^\d+$/.test(route.params.jobId);
  },
  middleware: [
    'require-auth',
  ],
});
</script>
