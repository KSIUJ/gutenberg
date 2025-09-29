<template>
  <app-panel
    v-if="printers.data.value === undefined || printers.data.value.length === 0"
    header="Print online"
  >
    <p-message
      v-if="printersErrorMessage !== null"
      severity="error"
    >
      {{ printersErrorMessage }}
    </p-message>
    <p-message
      v-else
      severity="info"
    >
      You do not have access to any printer
    </p-message>
  </app-panel>
  <app-panel
    v-else
    header="Print online"
    :header-clickable="!jobCreator.optionsExpanded"
    @header-click="jobCreator.expandOptions()"
  >
    <div>
      <div>
        <p-float-label variant="in">
          <p-select
            id="printer-select"
            v-model="jobCreator.selectedPrinterId"
            :options="printers.data.value"
            option-value="id"
            option-label="name"
            fluid
            :loading="printers.pending.value"
          />
          <label for="printer-select">Printer</label>
        </p-float-label>
      </div>

      <p-fieldset legend="Files">
        <template v-if="jobCreator.documents.length > 0">
          <document-list
            v-if="jobCreator.documents.length > 0"
            :documents="jobCreator.documents"
          />
          <p-divider />
        </template>
        <div>
          <div class="flex flex-row items-center gap-2">
            <p-file-upload
              mode="basic"
              auto
              choose-label="Choose files"
              custom-upload
              multiple
              :disabled="jobCreator.selectedPrinter === null"
              :accept="jobCreator.selectedPrinter?.supported_extensions"
              class="grow"
              :pt="{
                root: {
                  class: 'grow sm:grow-0 sm:shrink-0',
                },
              }"
              @select="onFileSelect"
            />
            <div class="hidden text-sm text-muted-color sm:block">
              or drop them anywhere
            </div>
          </div>
          <div
            v-if="jobCreator.selectedPrinter !== null"
            class="mt-2 px-1"
          >
            <div class="text-label">
              Supported file formats:
            </div>
            <div class="text-sm">
              {{ formatExtensions(jobCreator.selectedPrinter.supported_extensions) }}
            </div>
          </div>
        </div>
      </p-fieldset>

      <div
        class="space-y-4"
        :class="{
          hidden: !jobCreator.optionsExpanded,
        }"
      >
        <h2 class="mt-8 text-header">
          Processing options
        </h2>

        <!--      <label id="page-filter-select" class="text-label px-form">Filter printed pages</label> -->
        <!--      <SelectButton -->
        <!--        :options="pageFilterOptions" -->
        <!--        option-value="value" -->
        <!--        data-key="value" -->
        <!--        option-label="label" -->
        <!--        :allow-empty="false" -->
        <!--        fluid -->
        <!--        aria-labelledby="page-filter-select" -->
        <!--      /> -->

        <div>
          <p-float-label variant="in">
            <p-input-text
              v-model="jobCreator.pagesToPrint"
              fluid
              input-id="page-filter-input"
              aria-describedby="page-filter-input-description"
              placeholder="Print all pages"
            />
            <label for="page-filter-input">Input page filter</label>
          </p-float-label>
          <input-hint id="page-filter-input-description">
            You can use comma-separated pages or page ranges, for example: <i class="text-nowrap">13-20, 25, 30-31</i>.
            The page filter is applied to each file separately.
          </input-hint>
        </div>

        <labeled-toggle
          v-model="jobCreator.fitToPageEnabled"
          label="Fit to page"
          input-id="fit-to-page-enabled"
        />

        <label
          id="n-up-select"
          class="text-label px-form"
        >Input pages on each final page (N-up)</label>
        <p-select-button
          v-model="jobCreator.nUp"
          :options="nUpOptions"
          :allow-empty="false"
          fluid
          aria-labelledby="n-up-select"
        />

        <h2 class="mt-8 text-header ">
          Printing options
        </h2>

        <p-float-label variant="in">
          <p-input-number
            v-model="jobCreator.copyCount"
            :min="1"
            :max="1000"
            show-buttons
            button-layout="stacked"
            fluid
            input-id="copy-number-input"
          />
          <label for="copy-number-input">Number of copies</label>
        </p-float-label>

        <template v-if="jobCreator.selectedPrinter?.duplex_supported">
          <labeled-toggle
            v-model="duplexEnabled"
            label="Enable two&dash;sided printing"
            input-id="duplex-enabled"
          />

          <template v-if="jobCreator.duplexMode !== 'disabled'">
            <label
              id="duplex-mode-select"
              class="text-label px-form"
            >Flip backside around</label>
            <p-select-button
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
                  {{ option.label }}<br>
                  <span class="text-xs">({{ option.description }})</span>
                </div>
              </template>
            </p-select-button>
          </template>
        </template>

        <div>
          <label
            id="color-mode-select"
            class="text-label px-form"
          >Color mode</label>
          <p-select-button
            v-model="jobCreator.colorMode"
            :options="colorOptions"
            option-value="value"
            data-key="value"
            option-label="label"
            option-disabled="disabled"
            :allow-empty="false"
            fluid
            aria-labelledby="color-mode-select"
          >
            <template #option="{ option }">
              <div class="w-full">
                {{ option.label }}<br>
                <div class="mx-auto mt-2 mb-1 flex w-1/4 flex-row overflow-hidden rounded-xs">
                  <div
                    v-for="(color, i) in option.colors"
                    :key="i"
                    :class="[color, 'h-1', 'grow']"
                  />
                </div>
              </div>
            </template>
          </p-select-button>
          <input-hint v-if="jobCreator.selectedPrinter?.color_allowed === false">
            The selected printer does not support color printing or you do not have permission to use it
          </input-hint>
        </div>

        <p-message
          v-for="error in jobCreator.errorMessageList"
          :key="`${error.field ?? '-'}|${error.message}`"
          severity="error"
        >
          {{ error.message }}
        </p-message>
      </div>
    </div>

    <template
      v-if="jobCreator.optionsExpanded"
      #actions
    >
      <p-button
        label="Print"
        severity="primary"
        :loading="jobCreator.printLoading"
        @click="jobCreator.print"
      />
      <p-button
        label="Preview"
        severity="secondary"
        disabled
        @click="preview()"
      />
    </template>
  </app-panel>
  <file-drop-target @files-dropped="(files) => jobCreator.addFiles(files)" />
</template>

<script setup lang="ts">
import type { FileUploadSelectEvent } from 'primevue';

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
const colorOptions = computed(() => [
  {
    value: 'monochrome' as ColorMode,
    label: 'Grayscale',
    colors: ['bg-gray-300', 'bg-gray-400', 'bg-gray-500'],
    disabled: false,
  },
  {
    value: 'color' as ColorMode,
    label: 'Colored',
    colors: ['bg-cyan-300', 'bg-fuchsia-500', 'bg-yellow-300'],
    disabled: jobCreator.selectedPrinter?.color_allowed === false,
  },
]);

// const pageFilterOptions = [
//   { value: 'all', label: 'All' },
//   { value: 'odd', label: 'Odd' },
//   { value: 'even', label: 'Even' },
//   { value: 'custom', label: 'Custom' },
// ];

const nUpOptions = [1, 2, 4, 8, 16, 32];

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
