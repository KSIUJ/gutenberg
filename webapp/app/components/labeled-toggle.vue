<template>
  <div class="flex w-full flex-row items-center">
    <label
      :id="inputId"
      class="grow pl-form"
    >{{ label }}</label>
    <p-toggle-switch
      v-model="model"
      :aria-labelledby="inputId"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  inputId: string;
}>();

const model = defineModel<boolean>({
  default: false,
});
</script>
