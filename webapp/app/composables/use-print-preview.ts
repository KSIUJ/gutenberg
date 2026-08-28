import { useIntervalFn } from '@vueuse/core';

// Poll once a second while a preview is generating.
const POLL_INTERVAL_MS = 1000;

export type PrintPreviewPanelStatus = 'idle' | 'preparing' | 'generating' | 'ready' | 'failed';

/**
 * Manages requesting and polling a print preview for the job tracked by `jobCreator`. A preview
 * can only be requested once a real job exists with documents uploaded and properties saved.
 * `jobCreator.ensureJobUpToDate()` guarantees that, so every request starts by calling it.
 */
export const usePrintPreview = (jobCreator: ReturnType<typeof useJobCreator>) => {
  const apiRepository = useApiRepository();

  const visible = ref(false);
  const status = ref<PrintPreviewPanelStatus>('idle');
  const preview = ref<PrintPreview | null>(null);
  const errorMessage = ref<string | null>(null);
  const selectedPageNumber = ref<number | null>(null);

  const pages = computed(() => preview.value?.pages ?? []);

  const selectedPage = computed(() => {
    const byNumber = pages.value.find(page => page.number === selectedPageNumber.value);
    return byNumber ?? pages.value[0] ?? null;
  });

  const selectPage = (number: number) => {
    selectedPageNumber.value = number;
  };

  const applyPreview = (data: PrintPreview) => {
    preview.value = data;
    if (data.status === 'ready') {
      status.value = 'ready';
      if (!pages.value.some(page => page.number === selectedPageNumber.value)) {
        selectedPageNumber.value = pages.value[0]?.number ?? null;
      }
    } else if (data.status === 'pending' || data.status === 'processing') {
      status.value = 'generating';
    } else if (data.status === 'failed') {
      status.value = 'failed';
      errorMessage.value = data.error || 'Failed to generate the print preview';
    } else {
      // Canceled, most likely superseded by a newer generation request. Treat it as a failure
      // so the user is not left staring at a spinner that will never resolve
      status.value = 'failed';
      errorMessage.value = 'Preview generation was canceled';
    }
  };

  const poll = async () => {
    if (!visible.value || status.value !== 'generating' || jobCreator.jobId === null) return;
    try {
      applyPreview(await apiRepository.getJobPreview(jobCreator.jobId));
    } catch (pollError) {
      console.warn('Failed to poll print preview status', pollError);
    }
  };

  useIntervalFn(poll, POLL_INTERVAL_MS);

  const generate = async () => {
    status.value = 'preparing';
    errorMessage.value = null;
    try {
      const jobId = await jobCreator.ensureJobUpToDate();
      status.value = 'generating';
      applyPreview(await apiRepository.requestJobPreview(jobId));
    } catch (generationError) {
      console.error('Failed to request a print preview', generationError);
      status.value = 'failed';
      errorMessage.value = getErrorMessage(generationError) ?? 'Failed to generate the print preview';
    }
  };

  // Always regenerates rather than trying to detect whether anything changed since last time
  const open = async () => {
    visible.value = true;
    if (status.value === 'preparing' || status.value === 'generating') return;
    await generate();
  };

  const close = () => {
    visible.value = false;
  };

  return reactive({
    visible,
    status,
    pages,
    selectedPage,
    selectPage,
    errorMessage,
    open,
    close,
    regenerate: generate,
  });
};
