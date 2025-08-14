<template>
  <div class="w-full h-full flex flex-col">
    <div>
      <FloatLabel variant="in">
        <Select
          id="printer-select"
          :options="['Printer 1', 'Printer 2']"
          fluid
        />
        <label for="printer-select">Printer</label>
      </FloatLabel>
    </div>
    <FileUpload
      name="demo[]"
      multiple
      :show-upload-button="false"
      cancel-label="Clear"
      :pt="{
        root: 'grow my-4',
      }"
    >
      <template #empty>
        <span>Drag and drop files to here to upload.</span>
      </template>
    </FileUpload>
    <div class="space-y-4">
      <FloatLabel variant="in">
        <InputNumber
          v-model="copyCount"
          :min="1"
          :max="1000"
          show-buttons
          button-layout="stacked"
          fluid
          input-id="copy-number-input"
        />
        <label for="copy-number-input">Number of copies</label>
      </FloatLabel>

      <template v-if="duplexSupported">
        <div class="w-full flex flex-row items-center">
          <label id="duplex-enabled" class="grow">Enable two&dash;side printing</label>
          <ToggleSwitch
            v-model="duplexEnabled"
            aria-labelledby="duplex-enabled"
          />
        </div>

        <template v-if="duplexEnabled">
          <label id="duplex-mode-select">Flip backside around</label>
          <SelectButton
            v-model="duplexMode"
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

<!--      <label id="page-filter-select">Filter printed pages</label>-->
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

      <label id="color-mode-select">Color mode</label>
      <SelectButton
        v-model="colorMode"
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
    <div class="flex flex-row-reverse gap-2 pt-4 shrink-0">
      <Button label="Print" severity="primary" @click="print()" />
      <Button label="Preview" severity="secondary" @click="preview()" />
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

type DuplexMode = 'duplex-long-edge' | 'duplex-short-edge';
const duplexOptions = [
  { value: 'duplex-long-edge' as DuplexMode, label: 'Long edge', description: 'for vertical documents' },
  { value: 'duplex-short-edge' as DuplexMode, label: 'Short edge', description: 'for horizontal documents' },
];

type ColorMode = 'monochrome' | 'color';
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

const copyCount = ref(1);

const duplexSupported = ref(true);
const duplexEnabled = ref(false);
const duplexMode = ref<null | DuplexMode>(null);

const colorMode = ref<ColorMode>('monochrome');

watch(duplexEnabled, (value) => {
  if (!value) duplexMode.value = null;
}, { immediate: true })
</script>
