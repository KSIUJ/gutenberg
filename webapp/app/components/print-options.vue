<template>
  <div
    v-if="printers.data.value === undefined || printers.data.value.length === 0"
    class="w-full h-full py-2"
  >
    <message v-if="printersErrorMessage !== null" severity="error">{{ printersErrorMessage }}</message>
    <message v-else severity="info">You do not have access to any printer</message>
  </div>
  <div
    v-else
    class="w-full h-full flex flex-col space-y-6"
  >
    <div class="mb-0">
      <FloatLabel variant="in">
        <Select
          id="printer-select"
          v-model="jobCreator.selectedPrinterId"
          :options="printers.data.value"
          option-value="id"
          option-label="name"
          :default-value="null"
          fluid
          :loading="printers.pending.value"
        />
        <label for="printer-select">Printer</label>
      </FloatLabel>
    </div>

    <Fieldset legend="Files">
      <template v-if="jobCreator.documents.length > 0">
        <document-list
          v-if="jobCreator.documents.length > 0"
          :documents="jobCreator.documents"
        />
        <divider />
      </template>
      <div>
        <div class="flex flex-row space-x-2 items-center">
          <FileUpload
            mode="basic"
            class="w-full"
            auto
            choose-label="Choose files"
            custom-upload
            multiple
            :disabled="jobCreator.selectedPrinter === null"
            :accept="jobCreator.selectedPrinter?.supported_extensions"
            @select="onFileSelect"
          />
          <div class="text-muted-color text-sm">or drop them anywhere</div>
        </div>
        <div v-if="jobCreator.selectedPrinter !== null" class="mt-2 px-1">
          <div class="label-text">
            Supported file formats:
          </div>
          <div class="text-sm">{{ formatExtensions(jobCreator.selectedPrinter.supported_extensions) }}</div>
        </div>
      </div>
    </Fieldset>

<!--    <Button label="Refresh printer list" variant="text" @click="printers.refresh()" />-->
    <div class="space-y-4">
      <FloatLabel variant="in">
        <InputNumber
          v-model="jobCreator.copyCount"
          :min="1"
          :max="1000"
          show-buttons
          button-layout="stacked"
          fluid
          input-id="copy-number-input"
        />
        <label for="copy-number-input">Number of copies</label>
      </FloatLabel>

      <template v-if="jobCreator.selectedPrinter?.duplex_supported">
        <div class="w-full flex flex-row items-center">
          <label id="duplex-enabled" class="grow pl-form">Enable two&dash;side printing</label>
          <ToggleSwitch
            v-model="duplexEnabled"
            aria-labelledby="duplex-enabled"
          />
        </div>

        <template v-if="jobCreator.duplexMode !== 'disabled'">
          <label id="duplex-mode-select" class="label-text px-form">Flip backside around</label>
          <SelectButton
            v-model="jobCreator.duplexMode"
            :options="duplexOptions"
            option-value="value"
            data-key="value"
            option-label="label"
            :allow-empty="false"
            fluid
            aria-labelledby="duplex-mode-select"
          >
            <template #option="{ option }">
              <div>
                {{option.label}}<br>
                <span class="text-xs">({{option.description}})</span>
              </div>
            </template>
          </SelectButton>
        </template>
      </template>

<!--      <label id="page-filter-select" class="label-text px-form">Filter printed pages</label>-->
<!--      <SelectButton-->
<!--        :options="pageFilterOptions"-->
<!--        option-value="value"-->
<!--        data-key="value"-->
<!--        option-label="label"-->
<!--        :allow-empty="false"-->
<!--        fluid-->
<!--        aria-labelledby="page-filter-select"-->
<!--      />-->

<!--      <FloatLabel variant="in">-->
<!--        <InputText-->
<!--          fluid-->
<!--          input-id="page-filter-input"-->
<!--        />-->
<!--        <label for="page-filter-input">Page filter</label>-->
<!--      </FloatLabel>-->

      <label id="color-mode-select" class="label-text px-form">Color mode</label>
      <SelectButton
        v-model="jobCreator.colorMode"
        :options="colorOptions"
        option-value="value"
        data-key="value"
        option-label="label"
        :allow-empty="false"
        fluid
        aria-labelledby="color-mode-select"
      >
        <template #option="{ option }">
          <div class="w-full">
            {{option.label}}<br>
            <div class="w-1/4 flex flex-row mx-auto mt-2 mb-1 rounded-xs overflow-hidden">
              <div
                v-for="(color, i) in option.colors"
                :key="i"
                :class="[color, 'h-1', 'grow']"
              />
            </div>
          </div>
        </template>
      </SelectButton>
    </div>
    <Message
      v-for="error in jobCreator.errorMessageList"
      :key="error"
      severity="error"
    >
      {{ error }}
    </Message>
    <div class="flex flex-row-reverse gap-2 mt-4 shrink-0">
      <Button label="Print" severity="primary" :loading="jobCreator.printLoading" @click="jobCreator.print" />
      <Button label="Preview" severity="secondary" disabled @click="preview()" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type {FileUploadSelectEvent} from "primevue";

const printers = await usePrinters();
const jobCreator = useJobCreator(printers);

const printersErrorMessage = computed(() => {
  if (printers.error.value === undefined) return null;
  return getErrorMessage(printers.error.value) ?? 'Failed to load printer list';
});

const duplexOptions = [
  { value: 'duplex-long-edge' as DuplexMode, label: 'Long edge', description: 'for vertical documents' },
  { value: 'duplex-short-edge' as DuplexMode, label: 'Short edge', description: 'for horizontal documents' },
];
const duplexEnabled = computed({
  get: () => jobCreator.duplexMode !== 'disabled',
  set: (value) => {
    if (value && jobCreator.duplexMode === 'disabled') {
      jobCreator.duplexMode = 'duplex-unspecified';
    }
    if (!value) jobCreator.duplexMode = 'disabled';
  },
});

// Uses Tailwind color classes, see
// https://tailwindcss.com/docs/detecting-classes-in-source-files#how-classes-are-detected
const colorOptions = [
  {
    value: 'monochrome' as ColorMode,
    label: 'Grayscale',
    colors: ['bg-gray-300', 'bg-gray-400', 'bg-gray-500'],
  },
  {
    value: 'color' as ColorMode,
    label: 'Colored',
    colors: ['bg-cyan-300', 'bg-fuchsia-500', 'bg-yellow-300'],
  },
];

// const pageFilterOptions = [
//   { value: 'all', label: 'All' },
//   { value: 'odd', label: 'Odd' },
//   { value: 'even', label: 'Even' },
//   { value: 'custom', label: 'Custom' },
// ];

const onFileSelect = (event: FileUploadSelectEvent) => {
  jobCreator.addFiles(event.files);
};

const formatExtensions = (extensions: string) => {
  return extensions.split(',').map(ext => ext.trim()).join(', ');
};

function preview() {
  console.log('Preview clicked');
}
</script>
