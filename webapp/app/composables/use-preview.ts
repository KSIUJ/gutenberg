import { useIntervalFn } from '@vueuse/core';

const COMPLETED_PREVIEW_STATUSES: PreviewStatus[] = ['READY', 'FAILED', 'CANCELED'];

// Polls GET /api/jobs/{id}/preview/ while a generation is in progress, and
// exposes a `regenerate()` used whenever the user changes a print setting.
export const usePreview = (jobId: number) => {
  const apiRepository = useApiRepository();

  const preview = ref<PrintPreview | null>(null);
  const pending = ref(true);
  const error = ref<unknown | null>(null);

  const errorMessage = computed(() => {
    if (error.value === null) return null;
    return getErrorMessage(error.value) ?? 'Failed to load the print preview';
  });

  // True while there is no preview to show yet, or the current generation
  // has not finished processing - used to drive the loading state in the UI.
  const isGenerating = computed(() => {
    if (preview.value === null) return true;
    return !COMPLETED_PREVIEW_STATUSES.includes(preview.value.status);
  });

  const load = async () => {
    pending.value = true;
    error.value = null;
    try {
      preview.value = await apiRepository.getPreview(jobId);
    } catch (caught) {
      // A 404 here just means nobody has requested a preview for this job
      // yet, which is expected the very first time the panel opens.
      try {
        preview.value = await apiRepository.generatePreview(jobId);
      } catch (generateError) {
        error.value = generateError ?? caught;
      }
    } finally {
      pending.value = false;
    }
  };

  const regenerate = async () => {
    error.value = null;
    try {
      preview.value = await apiRepository.generatePreview(jobId);
    } catch (caught) {
      error.value = caught;
    }
  };

  const { pause, resume } = useIntervalFn(async () => {
    if (pending.value || preview.value === null) return;
    if (COMPLETED_PREVIEW_STATUSES.includes(preview.value.status)) return;
    try {
      preview.value = await apiRepository.getPreview(jobId);
    } catch (caught) {
      error.value = caught;
    }
  }, 1000);

  const cancel = async () => {
    pause();
    try {
      await apiRepository.cancelPreview(jobId);
    } catch (caught) {
      console.warn('Failed to cancel preview', caught);
    }
  };

  onBeforeUnmount(() => pause());

  load();

  return reactive({
    preview,
    pending,
    errorMessage,
    isGenerating,
    regenerate,
    cancel,
    pause,
    resume,
  });
};
