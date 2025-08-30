<template>
  <single-column-layout narrow>
    <app-panel>
      <p-message
        v-if="errorMessage !== null"
        severity="error"
      >
        {{ errorMessage }}
      </p-message>
      <div
        v-else-if="job.data.value !== undefined"
        class="space-y-4"
      >
        <p-stepper
          v-if="stepNumber !== null"
          linear
          :value="stepNumber"
        >
          <p-step-item :value="1">
            <p-step>
              Creating job
            </p-step>
            <p-step-panel>
              The print job has not been started yet.
            </p-step-panel>
          </p-step-item>
          <p-step-item :value="2">
            <p-step>
              Pending
            </p-step>
            <p-step-panel>
              Gutenberg has received all required information
              and should start processing the request shortly.
            </p-step-panel>
          </p-step-item>
          <p-step-item :value="3">
            <p-step>
              Processing
            </p-step>
            <p-step-panel>
              Gutenberg is processing the request.
            </p-step-panel>
          </p-step-item>
          <p-step-item :value="4">
            <p-step>
              Printing
            </p-step>
            <p-step-panel>
              The request has been sent to the printer.
            </p-step-panel>
          </p-step-item>
          <p-step-item :value="5">
            <p-step>
              Completed
            </p-step>
          </p-step-item>
        </p-stepper>
        <p-message
          v-if="job.data.value.status === 'CANCELED' || job.data.value.status === 'CANCELING'"
          severity="warn"
        >
          <p>
            This print job has been cancelled.
          </p>
          <p
            v-if="job.data.value.status_reason"
            class="mt-3 text-sm"
          >
            {{ job.data.value.status_reason }}
          </p>
          <p class="mt-3 text-sm">
            Some pages might still get printed if the printer has already started processing the request.
          </p>
        </p-message>
        <p-message
          v-if="job.data.value.status === 'COMPLETED'"
          severity="success"
        >
          Your document is ready or will finish printing soon.<br>
          Thank you for using Gutenberg.
        </p-message>
        <p-message
          v-if="job.data.value.status === 'ERROR'"
          severity="error"
        >
          <p>
            This print job has failed.
          </p>
          <code
            v-if="job.data.value.status_reason"
            class="mt-3 block text-sm"
          >
            {{ job.data.value.status_reason }}
          </code>
        </p-message>
        <p-message
          v-if="job.data.value.status === 'UNKNOWN'"
          severity="warn"
        >
          <p>
            This status of this print job is unknown.
          </p>
          <code
            v-if="job.data.value.status_reason"
            class="mt-3 block text-sm"
          >
            {{ job.data.value.status_reason }}
          </code>
        </p-message>
      </div>

      <template
        v-if="cancelable"
        #actions
      >
        <p-button
          v-if="cancelable"
          severity="danger"
          label="Cancel"
          :loading="cancelLoading"
          variant="text"
          @click="cancelJob"
        />
      </template>
    </app-panel>
  </single-column-layout>
</template>

<script setup lang="ts">
import { useIntervalFn } from '@vueuse/core';

const COMPLETED_STATUES: JobStatus[] = ['COMPLETED', 'ERROR', 'CANCELED', 'UNKNOWN'];
const STATUS_TO_STEP_MAP: Record<JobStatus, number | null> = {
  INCOMING: 1,
  PENDING: 2,
  PROCESSING: 3,
  PRINTING: 4,
  COMPLETED: 5,
  // For these statuses the stepper is not displayed
  ERROR: null,
  CANCELED: null,
  CANCELING: null,
  UNKNOWN: null,
};

const apiRepository = useApiRepository();
const route = useRoute();
const toast = useToast();

const jobId = computed(() => parseInt(route.params.jobId as string, 10));
const job = await useAsyncData(
  () => apiRepository.getJob(jobId.value),
  { watch: [jobId] },
);
watch(() => job.error.value, (error) => {
  if (error === undefined) return;
  console.error(error);
}, { immediate: true });

useIntervalFn(() => {
  if (job.pending.value || !job.data.value) return;
  if (COMPLETED_STATUES.includes(job.data.value.status)) return;
  job.refresh().catch();
}, 1000);

const errorMessage = computed(() => {
  if (job.error.value) {
    return getErrorMessage(job.error.value) ?? 'Failed to load print job details';
  }
  return null;
});

const cancelable = computed(() => {
  if (!job.data.value) return false;
  return !COMPLETED_STATUES.includes(job.data.value.status) && job.data.value.status !== 'CANCELING';
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

const stepNumber = computed<number | null>(() => {
  if (!job.data.value) return null;
  return STATUS_TO_STEP_MAP[job.data.value.status];
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
