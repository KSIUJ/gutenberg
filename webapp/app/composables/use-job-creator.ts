import type { NuxtError } from '#app';
import type { _AsyncData } from '#app/composables/asyncData';

export type DuplexMode = 'disabled' | 'duplex-unspecified' | 'duplex-long-edge' | 'duplex-short-edge';
export type ColorMode = 'monochrome' | 'color';

export type JobDocument = {
  localId: number;
  filename: string;
  file: File;
  state: 'pending' | 'uploading' | 'uploaded' | 'error';
  remove(): void;
};

export type JobCreationError = {
  field: keyof CreatePrintJobRequest | (string & {}) | null;
  message: string;
};

const twoSidesMapping = {
  'disabled': 'OS',
  'duplex-long-edge': 'TL',
  'duplex-short-edge': 'TS',
} satisfies Record<Exclude<DuplexMode, 'duplex-unspecified'>, ApiDuplexMode>;

export const useJobCreator = (printers: _AsyncData<Printer[] | undefined, NuxtError | undefined>) => {
  const apiRepository = useApiRepository();
  const toast = useToast();

  const getDefaultPrinter = () => {
    return printers.data.value?.at(0) ?? null;
  };

  const selectedPrinterId = ref(getDefaultPrinter()?.id ?? null);
  const documentQueue = ref<JobDocument[]>([]);
  const copyCount = ref(1);
  const duplexMode = ref<DuplexMode>('disabled');
  const colorMode = ref<ColorMode>('monochrome');

  const printLoading = ref(false);
  const printError = ref<unknown | null>(null);
  const showSerializationErrors = ref(false);
  const optionsExpanded = ref(false);

  const selectedPrinter = computed(() => {
    if (selectedPrinterId.value === null) return null;
    if (!printers.data.value) return null;
    return printers.data.value.find(printer => printer.id === selectedPrinterId.value) ?? null;
  });

  watchEffect(() => {
    if (printers.data.value === undefined) return;

    const firstPrinter = printers.data.value.at(0) ?? null;
    if (selectedPrinterId.value === null && firstPrinter !== null) {
      selectedPrinterId.value = firstPrinter.id;
    } else if (selectedPrinterId.value !== null && selectedPrinter.value === null) {
      selectedPrinterId.value = firstPrinter?.id ?? null;
      toast.add({
        severity: 'warn',
        summary: 'The previously selected printer is no longer available',
        detail: firstPrinter === null ? undefined : `The printer "${firstPrinter.name}" was selected instead`,
      });
    }
  });

  // Automatically change the settings to their default values if the selected printer
  // does not support changing them.
  //
  // The automatic change is required because the UI inputs for unsupported settings get hidden.
  watchEffect(() => {
    if (selectedPrinter.value === null) return;
    if (duplexMode.value !== 'disabled' && !selectedPrinter.value.duplex_supported) {
      duplexMode.value = 'disabled';
      toast.add({
        severity: 'warn',
        summary: 'Disabled two-side printing',
        detail: 'The selected printer does not support it',
      });
    }
    if (colorMode.value === 'color' && !selectedPrinter.value.color_allowed) {
      colorMode.value = 'monochrome';
      toast.add({
        severity: 'warn',
        summary: 'Disabled color printing',
        detail: 'The selected printer does not support color printing or you do not have permission to use it',
      });
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
    };
  });

  const errorMessageList = computed<JobCreationError[]>(() => {
    const list: JobCreationError[] = [];
    if (printers.error.value !== undefined) {
      list.push({
        field: 'printer',
        message: getErrorMessage(printers.error.value) ?? 'Failed to get printer list',
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
    documentQueue.value.push(...files.map(file => reactive({
      localId: nextLocalFileId++,
      file,
      filename: file.name,
      state: 'pending' as const,
      remove() {
        if (printLoading.value) return;
        documentQueue.value = documentQueue.value.filter(
          document => document.localId !== this.localId,
        );
      },
    })));
    optionsExpanded.value = true;
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
      await apiRepository.uploadArtefact(jobId, document.file, isLast);
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
    await navigateTo(`/print/jobs/${jobId}/`);
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
    optionsExpanded: readonly(optionsExpanded),
  });
};
