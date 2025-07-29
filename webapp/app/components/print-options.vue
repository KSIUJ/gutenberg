<template>
  <FloatLabel variant="in">
    <Select
      id="printer-select"
      :options="['Printer 1', 'Printer 2']"
      class="w-full"
    />
    <label for="printer-select">Printer</label>
  </FloatLabel>
  <div class="flex flex-row-reverse gap-2 pt-4">
    <Button severity="primary" @click="print()">
      Print
    </Button>
    <Button severity="secondary" @click="preview()">
      Preview
    </Button>
  </div>
</template>

<script setup lang="ts">
import Button from "primevue/button";
import FloatLabel from "primevue/floatlabel";
import Select from "primevue/select";

function preview() {
  console.log('Preview clicked');
}

function print() {
  console.log('Print clicked');
}
</script>
