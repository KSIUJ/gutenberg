import type {NuxtError} from "#app";
import type {_AsyncData} from "#app/composables/asyncData";

export type DuplexMode = 'disabled' | 'duplex-unspecified' | 'duplex-long-edge' | 'duplex-short-edge';
export type ColorMode = 'monochrome' | 'color';

export const useJobCreator = (printers: _AsyncData<Printer[] | undefined, NuxtError | undefined>) => {
  const apiRepository = useApiRepository();

  const selectedPrinterId = ref(null);
  const selectedPrinter = computed(() => {
    if (selectedPrinterId.value === null) return null;
    if (!printers.data.value) return null;
    return printers.data.value.find((printer) => printer.id === selectedPrinterId.value) ?? null;
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

  const fileQueue = ref<File[]>([]);

  const addFiles = (files: File[]) => {
    fileQueue.value.push(...files);
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

  const completePrintJob = async (jobId: number) => {
    try {
      const files = [...fileQueue.value];
      for (const [index, file] of files.entries()) {
        const isLast = index == files.length - 1;
        await apiRepository.uploadArtefact(jobId, file, isLast);
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
    print,
    printLoading,
  });
};
