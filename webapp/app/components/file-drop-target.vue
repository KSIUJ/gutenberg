<template>
  <teleport
    v-if="overlayVisible"
    to="body"
  >
    <div class="pointer-events-none overlay z-50 fixed inset-0 bg-primary-800 opacity-90 text-white text-center flex items-center justify-center p-8">
      <div class="text-3xl">
        Drop files to add them
      </div>
    </div>
  </teleport>
</template>

<script lang="ts" setup>
/**
 * When this component is mounted, it will capture all file drop events, with the document root
 * as the target.
 *
 * When a file is dragged, an overlay over the entire document will be shown.
 *
 * Dropped files are emitted in the `filesDropped` event.
 */
import { useDropZone, autoResetRef, useDebounce } from '@vueuse/core';

const emit = defineEmits<{
  filesDropped: [files: File[]];
}>();

const fileDropOverlayVisibleCount = ref(0);
// Automatically hide the overlay after a delay to prevent getting stuck in the dropping state
// for any reason.
const overlayDisplayedRecently = autoResetRef(false, 10000);

// Debounce to prevent flickering when the fileDropOverlayVisibleCount momentarily drops to 0.
const overlayVisible = useDebounce(computed(
  () => overlayDisplayedRecently.value && fileDropOverlayVisibleCount.value > 0,
), 50);

useDropZone(document.documentElement, {
  multiple: true,
  preventDefaultForUnhandled: true,
  onEnter: () => {
    fileDropOverlayVisibleCount.value++;
    overlayDisplayedRecently.value = true;
  },
  onOver: () => {
    overlayDisplayedRecently.value = true;
  },
  onDrop: (files) => {
    fileDropOverlayVisibleCount.value--;
    if (files === null) return;
    emit('filesDropped', files);
  },
  onLeave: () => {
    fileDropOverlayVisibleCount.value--;
  },
});
</script>
