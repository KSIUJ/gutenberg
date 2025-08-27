import type {NuxtError} from "#app";
import type {_AsyncData} from "#app/composables/asyncData";

export type DuplexMode = 'disabled' | 'duplex-unspecified' | 'duplex-long-edge' | 'duplex-short-edge';
export type ColorMode = 'monochrome' | 'color';

export type JobDocument = {
  localId: number;
  filename: string;
  file: File;
  state: 'pending' | 'uploading' | 'uploaded' | 'error';
  remove(): void,
};

export type JobCreationError = {
  field: keyof CreatePrintJobRequest | (string & {}) | null;
  message: string;
};

const twoSidesMapping = {
  disabled: "OS",
  "duplex-long-edge": "TL",
  "duplex-short-edge": "TS",
} satisfies Record<Exclude<DuplexMode, 'duplex-unspecified'>, ApiDuplexMode>;

export const useJobCreator = (printers: _AsyncData<Printer[] | undefined, NuxtError | undefined>) => {
  const apiRepository = useApiRepository();

  const getFirstPrinterId = () => {
    return printers.data.value?.at(0)?.id ?? null;
  };

  const selectedPrinterId = ref(getFirstPrinterId());
  const documentQueue = ref<JobDocument[]>([]);
  const copyCount = ref(1);
  const duplexMode = ref<DuplexMode>('disabled');
  const colorMode = ref<ColorMode>('monochrome');

  const printLoading = ref(false);
  const printError = ref<unknown | null>(null);
  const showSerializationErrors = ref(false);

  const selectedPrinter = computed(() => {
    if (selectedPrinterId.value === null) return null;
    if (!printers.data.value) return null;
    return printers.data.value.find((printer) => printer.id === selectedPrinterId.value) ?? null;
  });

  watchEffect(() => {
    if (printers.data.value === undefined) return;

    // If no printer is selected or the selected printer is not on the printer list,
    // select the first printer (or deselect if the printer list is empty).
    if (selectedPrinterId.value === null || selectedPrinter.value === null) {
      selectedPrinterId.value = getFirstPrinterId();
    }
  });

  // These settings do not show up the UI if they are not available.
  watchEffect(() => {
    if (selectedPrinter.value === null) return;
    if (duplexMode.value !== 'disabled' && !selectedPrinter.value.duplex_supported) {
      duplexMode.value = 'disabled';
    }
    if (colorMode.value === 'color' && !selectedPrinter.value.color_allowed) {
      colorMode.value = 'monochrome';
    }
  });

  const serializedSettings = computed(() => {
    const errors: JobCreationError[] = [];

    if (selectedPrinterId.value === null) {
      errors.push({
        field: 'printer',
        message: 'No printer selected',
      });
    }

    let two_sides: ApiDuplexMode | undefined;
    if (duplexMode.value === 'duplex-unspecified') {
      errors.push({
        field: 'two_sides',
        message: 'Two-side printing mode not selected',
      });
      two_sides = undefined;
    } else {
      two_sides = twoSidesMapping[duplexMode.value];
    }

    if (documentQueue.value.length === 0) {
      errors.push({
        field: null,
        message: 'No documents selected',
      });
    }

    if (errors.length > 0 || two_sides === undefined || selectedPrinterId.value === null) {
      return {
        errors,
        request: null,
      };
    }

    const request = {
      printer: selectedPrinterId.value,
      copies: copyCount.value,
      pages_to_print: undefined,
      two_sides,
      color: colorMode.value === 'color',
      fit_to_page: undefined,
    } satisfies CreatePrintJobRequest;
    return {
      errors,
      request,
    }
  });

  const errorMessageList = computed<JobCreationError[]>(() => {
    const list: JobCreationError[] = [];
    if (printers.error.value !== undefined) {
      list.push({
        field: 'printer',
        message: getErrorMessage(printers.error.value) ?? 'Failed to get printer list'
      });
    }
    if (showSerializationErrors.value) {
      list.push(...serializedSettings.value.errors);
    }
    if (printError.value !== null) {
      list.push({
        field: null,
        message: getErrorMessage(printError.value) ?? 'Failed to create print job',
      });
    }
    return list;
  });

  let nextLocalFileId = 0;
  const addFiles = (files: File[]) => {
    documentQueue.value.push(...files.map((file) => reactive({
      localId: nextLocalFileId++,
      file,
      filename: file.name,
      state: 'pending' as const,
      remove() {
        if (printLoading.value) return;
        documentQueue.value = documentQueue.value.filter(
          (document) => document.localId !== this.localId,
        );
      },
    })));
  };

  const tryCancel = async (jobId: number) => {
    try {
      await apiRepository.cancelPrintJob(jobId);
    } catch (error) {
      console.warn('Failed to cancel job after error', error);
    }
  };

  const uploadDocument = async (jobId: number, document: JobDocument, isLast: boolean) => {
    if (document.state !== 'pending' && document.state !== 'error') return;
    try {
      document.state = 'uploading';
      await apiRepository.uploadArtefact(jobId, document.file, isLast)
      document.state = 'uploaded';
    } catch (error) {
      document.state = 'error';
      throw error;
    }
  };

  const completePrintJob = async (jobId: number) => {
    try {
      const documents = [...documentQueue.value];
      for (const document of documents) {
        await uploadDocument(jobId, document, false);
      }
      await apiRepository.runJob(jobId);
    } catch (error) {
      await tryCancel(jobId);
      throw error;
    }
    await navigateTo(`/jobs/${jobId}/`);
  };

  const print = async () => {
    showSerializationErrors.value = true;
    if (printLoading.value || serializedSettings.value.request === null) return;

    try {
      printLoading.value = true;
      printError.value = null;
      documentQueue.value.forEach((document) => {
        document.state = 'pending';
      });
      const job = await apiRepository.createPrintJob(serializedSettings.value.request);
      await completePrintJob(job.id);
    } catch (error) {
      console.error('Failed to create print job', error);
      printError.value = error;
    } finally {
      printLoading.value = false;
    }
  };

  return reactive({
    printers,
    selectedPrinterId,
    selectedPrinter,
    copyCount,
    duplexMode,
    colorMode,
    errorMessageList,
    addFiles,
    documents: readonly(documentQueue),
    print,
    printLoading,
  });
};
