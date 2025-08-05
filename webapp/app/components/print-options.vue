<template>
  <div class="w-full h-full flex flex-col">
    <FileUpload
      name="demo[]"
      multiple
      :show-upload-button="false"
      cancel-label="Clear"
      :pt="{
        root: 'grow mb-4',
      }"
    >
      <template #empty>
        <span>Drag and drop files to here to upload.</span>
      </template>
    </FileUpload>
    <div class="space-y-4">
      <FloatLabel variant="in">
        <Select
          id="printer-select"
          :options="['Printer 1', 'Printer 2']"
          fluid
        />
        <label for="printer-select">Printer</label>
      </FloatLabel>
      <FloatLabel variant="in">
        <InputNumber
          :min="1"
          show-buttons
          button-layout="stacked"
          fluid
          input-id="copy-number-input"
        />
        <label for="copy-number-input">Number of copies</label>
      </FloatLabel>

      <div class="w-full flex flex-row items-center">
        <label id="duplex-enabled" class="grow">Enable two&dash;side printing</label>
        <ToggleSwitch aria-labelledby="duplex-enabled" />
      </div>

      <label id="duplex-mode-select">Flip backside around</label>
      <SelectButton
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

      <label id="page-filter-select">Filter printed pages</label>
      <SelectButton
        :options="pageFilterOptions"
        option-value="value"
        data-key="value"
        option-label="label"
        :allow-empty="false"
        fluid
        aria-labelledby="page-filter-select"
      />

      <FloatLabel variant="in">
        <InputText
          fluid
          input-id="page-filter-input"
        />
        <label for="page-filter-input">Page filter</label>
      </FloatLabel>

      <label id="colored-select">Color mode</label>
      <SelectButton
        :options="colorOptions"
        option-value="value"
        data-key="value"
        option-label="label"
        :allow-empty="false"
        fluid
        aria-labelledby="colored-select"
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
    <div class="flex flex-row-reverse gap-2 pt-4 shrink-0">
      <Button severity="primary" @click="print()">
        Print
      </Button>
      <Button severity="secondary" @click="preview()">
        Preview
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
function preview() {
  console.log('Preview clicked');
}

function print() {
  console.log('Print clicked');
}

const duplexOptions = [
  { value: 'long', label: 'Long edge', description: 'for vertical documents' },
  { value: 'short', label: 'Short edge', description: 'for horizontal documents' },
];

// Uses Tailwind color classes, see
// https://tailwindcss.com/docs/detecting-classes-in-source-files#how-classes-are-detected
const colorOptions = [
  {
    value: false, label: 'Grayscale',
    colors: ['bg-gray-300', 'bg-gray-400', 'bg-gray-500'],
  },
  {
    value: true, label: 'Colored',
    colors: ['bg-cyan-300', 'bg-fuchsia-500', 'bg-yellow-300'],
  },
];

const pageFilterOptions = [
  { value: 'all', label: 'All' },
  { value: 'odd', label: 'Odd' },
  { value: 'even', label: 'Even' },
  { value: 'custom', label: 'Custom' },
];
</script>
