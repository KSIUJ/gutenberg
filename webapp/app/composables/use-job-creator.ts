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

export const useJobCreator = (printers: _AsyncData<Printer[] | undefined, NuxtError | undefined>) => {
  const apiRepository = useApiRepository();

  const getFirstPrinterId = () => {
    return printers.data.value?.at(0)?.id ?? null;
  };

  const selectedPrinterId = ref(getFirstPrinterId());
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

  const copyCount = ref(1);
  const duplexMode = ref<DuplexMode>('disabled');
  const colorMode = ref<ColorMode>('monochrome');

  watchEffect(() => {
    if (duplexMode.value !== 'disabled' && selectedPrinter.value?.duplex_supported === false) {
      duplexMode.value = 'disabled';
    }
  });

  const serializedSettings = computed<CreatePrintJobRequest | null>(() => {
    if (selectedPrinterId.value === null) return null;
    if (duplexMode.value === 'duplex-unspecified') return null;

    const twoSidesMapping = {
      disabled: "OS",
      "duplex-long-edge": "TL",
      "duplex-short-edge": "TS",
    } satisfies Record<Exclude<DuplexMode, 'duplex-unspecified'>, ApiDuplexMode>;

    return {
      printer: selectedPrinterId.value,
      copies: copyCount.value,
      pages_to_print: undefined,
      two_sides: twoSidesMapping[duplexMode.value],
      color: colorMode.value === 'color',
      fit_to_page: undefined,
    };
  });

  const documentQueue = ref<JobDocument[]>([]);

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

  const printLoading = ref(false);
  const printError = ref<unknown | null>(null);

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
      for (const [index, document] of documents.entries()) {
        const isLast = index == documents.length - 1;
        await uploadDocument(jobId, document, isLast);
      }
    } catch (error) {
      await tryCancel(jobId);
      throw error;
    }
  };

  const print = async () => {
    if (printLoading.value || serializedSettings.value === null) return;
    // TODO: Do not start if the job contains no files

    try {
      printLoading.value = true;
      printError.value = null;
      documentQueue.value.forEach((document) => {
        document.state = 'pending';
      });
      const job = await apiRepository.createPrintJob(serializedSettings.value);
      await completePrintJob(job.id);
    } catch (error) {
      console.error('Failed to create print job', error);
      printError.value = error;
    } finally {
      printLoading.value = false;
    }
  };

  const errorMessageList = computed(() => {
    const list = [];
    if (printers.error.value !== undefined) {
      list.push(getErrorMessage(printers.error.value) ?? 'Failed to get printer list');
    }
    if (printError.value !== null) {
      list.push(getErrorMessage(printError.value) ?? 'Failed to create print job');
    }
    return list;
  });

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
