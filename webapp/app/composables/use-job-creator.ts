import type { NuxtError } from '#app';
import type { _AsyncData } from '#app/composables/asyncData';
import { collectResultsObject, error, type Result } from '~/utils/results';

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

export type JobResult<T> = Result<T, JobCreationError>;

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
  const fitToPageEnabled = ref(true);
  const pagesToPrint = ref<string>('');
  const nUp = ref<number>(1);

  const printLoading = ref(false);
  const printError = ref<unknown | null>(null);
  const showSerializationErrors = ref(false);

  const optionsExpanded = ref(false);
  const expandOptions = () => {
    optionsExpanded.value = true;
  };

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

  const serializePrinterId = (): JobResult<number> => {
    if (selectedPrinterId.value === null) {
      return error({
        field: 'printer',
        message: 'No printer selected',
      });
    }
    return ok(selectedPrinterId.value);
  };

  const serializeDuplexMode = (): JobResult<ApiDuplexMode> => {
    if (duplexMode.value === 'duplex-unspecified') {
      return error({
        field: 'two_sides',
        message: 'Two-side printing mode not selected',
      });
    }
    return ok(twoSidesMapping[duplexMode.value]);
  };

  const serializePagesToPrint = (): JobResult<string | undefined> => {
    if (pagesToPrint.value.trim() === '') {
      return ok(undefined);
    }
    const { errors, value: parts } = collectResultArray(
      pagesToPrint.value
        .split(',')
        .map(part => part.trim())
        .map((part): JobResult<{ start: number; end: number }> => {
          if (part === '') return error({
            field: 'pages_to_print',
            message: 'Invalid empty page range',
          });

          const rangeRegex = /^(\d+)(?:\s*-\s*(\d+))?$/;
          const match = rangeRegex.exec(part);
          if (match === null) return error({
            field: 'pages_to_print',
            message: `Invalid page range: "${part}"`,
          });
          const start = parseInt(match[1]!);
          const end = match[2] === undefined ? start : parseInt(match[2]);
          if (isNaN(start) || isNaN(end) || start > end) return error({
            field: 'pages_to_print',
            message: `Invalid page range: "${part}"`,
          });
          return ok({ start, end });
        }),
    );

    // Return only the first error
    if (errors !== null) return error(...(errors.slice(0, 1)));

    for (let i = 1; i < parts.length; i++) {
      if (parts[i]!.start <= parts[i - 1]!.end) return error({
        field: 'pages_to_print',
        message: 'Page ranges must be sorted and non-overlapping',
      });
    }

    return ok(parts
      .map(part => `${part.start}-${part.end}`)
      .join(','),
    );
  };

  const serializedSettings = computed<Result<CreatePrintJobRequest, JobCreationError>>(() => {
    // These fields cannot be serialized if their values are not valid.
    // The serializeX functions do not throw, but return a custom `Result` type instead,
    // so all errors can be collected.
    const result = collectResultsObject({
      printer: serializePrinterId(),
      two_sides: serializeDuplexMode(),
      pages_to_print: serializePagesToPrint(),
    });

    // The serialization will also fail if this list is not empty
    const validationErrors: JobCreationError[] = [];
    if (documentQueue.value.length === 0) {
      validationErrors.push({
        field: null,
        message: 'No documents selected',
      });
    }

    if (result.errors !== null || validationErrors.length > 0) {
      return error(
        ...result.errors ?? [],
        ...validationErrors,
      );
    }

    const request = {
      ...result.value,
      copies: copyCount.value,
      color: colorMode.value === 'color',
      fit_to_page: fitToPageEnabled.value,
      n_up: nUp.value,
    } satisfies CreatePrintJobRequest;
    return ok(request);
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
      list.push(...serializedSettings.value.errors ?? []);
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
    if (printLoading.value || serializedSettings.value.value === null) return;

    try {
      printLoading.value = true;
      printError.value = null;
      documentQueue.value.forEach((document) => {
        document.state = 'pending';
      });
      const job = await apiRepository.createPrintJob(serializedSettings.value.value);
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
    fitToPageEnabled,
    pagesToPrint,
    nUp,
    errorMessageList,
    addFiles,
    documents: readonly(documentQueue),
    print,
    printLoading,
    optionsExpanded: readonly(optionsExpanded),
    expandOptions,
  });
};
