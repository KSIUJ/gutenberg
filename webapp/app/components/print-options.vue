<template>
  <div class="w-full">
    <div class="space-y-4">
      <FileUpload
        name="demo[]"
        multiple
        :show-upload-button="false"
        cancel-label="Clear"
      >
        <template #empty>
          <span>Drag and drop files to here to upload.</span>
        </template>
      </FileUpload>
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

      <label id="duplex-mode-select">Flip around</label>
      <SelectButton
          :options="duplexOptions"
          option-value="value"
          data-key="value"
          option-label="label"
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

      <label id="colored-select">Color mode</label>
      <SelectButton
        :options="colorOptions"
        option-value="value"
        data-key="value"
        option-label="label"
        fluid
        aria-labelledby="colored-select"
      />
    </div>
    <div class="flex flex-row-reverse gap-2 pt-4">
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
import Button from "primevue/button";
import FloatLabel from "primevue/floatlabel";
import Select from "primevue/select";
import FileUpload from "primevue/fileupload";
import InputNumber from "primevue/inputnumber";
import SelectButton from "primevue/selectbutton";
import ToggleSwitch from "primevue/toggleswitch";

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
const colorOptions = [
  { value: false, label: 'Grayscale' },
  { value: true, label: 'Colored' },
];
</script>
