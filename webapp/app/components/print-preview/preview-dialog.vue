<template>
  <!-- Teleported to <body>, full-screen on mobile, centered card on desktop. -->
  <teleport to="body">
    <div
      v-if="preview.visible"
      ref="dialogRef"
      class="fixed inset-0 z-50 flex flex-col bg-surface-0 sm:items-center sm:justify-center sm:bg-transparent"
      role="dialog"
      aria-modal="true"
      aria-label="Print preview"
      tabindex="-1"
      @keydown.esc="preview.close()"
      @keydown.left="goPrevUnit"
      @keydown.right="goNextUnit"
    >
      <div
        class="hidden sm:absolute sm:inset-0 sm:block sm:bg-black/40"
        @click="preview.close()"
      />

      <div
        class="relative flex h-full w-full flex-col overflow-hidden bg-surface-0 sm:h-[min(90vh,56rem)] sm:w-[min(90vw,52rem)] sm:rounded-border sm:border sm:border-surface sm:shadow-lg"
      >
        <!-- Header -->
        <div class="flex shrink-0 items-center gap-2 border-b border-surface px-4 py-3">
          <div class="min-w-0 grow">
            <h2 class="truncate text-header">
              Print preview
            </h2>
            <p
              v-if="unitPositionLabel"
              class="text-xs text-muted-color"
            >
              {{ unitPositionLabel }}
            </p>
          </div>
          <p-button
            aria-label="Close preview"
            severity="secondary"
            variant="text"
            rounded
            class="shrink-0"
            @click="preview.close()"
          >
            <svg
              viewBox="0 0 20 20"
              fill="none"
              class="size-5"
            >
              <path
                d="M5 5l10 10M15 5L5 15"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
              />
            </svg>
          </p-button>
        </div>

        <!-- Main viewer -->
        <div class="relative flex min-h-0 grow items-center justify-center gap-2 bg-surface-50 p-3 sm:gap-4 sm:p-6">
          <template v-if="preview.status === 'preparing'">
            <preview-status-message>
              Uploading documents and saving your settings…
            </preview-status-message>
          </template>
          <template v-else-if="preview.status === 'generating'">
            <preview-status-message>
              Generating preview…
            </preview-status-message>
          </template>
          <template v-else-if="preview.status === 'failed'">
            <preview-status-message variant="error">
              {{ preview.errorMessage ?? 'Failed to generate the print preview.' }}
              <template #action>
                <p-button
                  label="Try again"
                  severity="secondary"
                  variant="outlined"
                  size="small"
                  class="mt-2"
                  @click="preview.regenerate()"
                />
              </template>
            </preview-status-message>
          </template>
          <template v-else-if="selectedUnit === null">
            <preview-status-message variant="error">
              This job does not contain any pages to print.
            </preview-status-message>
          </template>
          <template v-else>
            <!-- A "unit" is one printed side, or a front/back pair for duplex/booklet. Using one
                 concept for both means the nav/selection logic only needs writing once. -->
            <p-button
              v-if="hasPrevUnit"
              aria-label="Previous page"
              severity="secondary"
              rounded
              raised
              class="shrink-0"
              @click="goPrevUnit"
            >
              <svg
                viewBox="0 0 20 20"
                fill="none"
                class="size-5"
              ><path
                d="M12 4l-6 6 6 6"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
                stroke-linejoin="round"
              /></svg>
            </p-button>

            <div class="flex h-full min-w-0 grow items-center justify-center overflow-hidden">
              <!-- This wrapper's `items-center` makes a child's `h-full` not resolve, since
                   centering a flex item sizes it to its content. The layouts below that need
                   `h-full` add `self-stretch` to opt back in. -->
              <preview-page-image
                v-if="!isPaired"
                :page="selectedUnit.pages[0]!"
                class="max-h-full max-w-full"
              />

              <!-- Booklet: front and back stacked on top of each other, each already containing
                   two source pages one above the other (the backend always merges them this way,
                   see `BookletImpositionProcessor`). So each row gets its own dashed horizontal
                   fold line. -->
              <div
                v-else-if="isBooklet"
                class="flex h-full w-full max-w-2xl shrink-0 flex-col gap-3 self-stretch"
              >
                <div
                  v-for="page in selectedUnit.pages"
                  :key="page.number"
                  class="flex min-h-0 flex-1 items-center justify-center"
                >
                  <!-- Explicit aspect-ratio instead of inline-block: a percentage max-height
                       only works if the element has a definite height, which a content-sized
                       inline-block box never has, so the image used to render full-size and get
                       clipped. -->
                  <div
                    class="relative max-h-full max-w-full"
                    :style="{ aspectRatio: `${page.width} / ${page.height}` }"
                  >
                    <preview-page-image
                      :page="page"
                      class="h-full w-full"
                    />
                    <div
                      class="pointer-events-none absolute inset-x-0 top-1/2 border-t-2 border-dashed border-surface-400"
                      aria-hidden="true"
                    />
                  </div>
                </div>
              </div>

              <!-- Two-sided: front left, back right, per docs/internals/ui-ux-design.md. -->
              <div
                v-else-if="duplexAxis !== null"
                class="flex h-full w-full max-w-2xl shrink-0 items-stretch justify-center gap-4 self-stretch"
              >
                <div class="flex min-w-0 flex-1 flex-col items-center gap-1">
                  <span class="text-xs font-medium text-muted-color">Front</span>
                  <preview-page-image
                    :page="selectedUnit.pages[0]!"
                    class="min-h-0 max-w-full grow"
                  />
                </div>
                <div class="flex min-w-0 flex-1 flex-col items-center gap-1">
                  <span class="text-xs font-medium text-muted-color">Back</span>
                  <preview-page-image
                    :page="selectedUnit.pages[1]!"
                    class="min-h-0 max-w-full grow"
                    :rotated="rotateBack180"
                  />
                  <span
                    v-if="rotateBack180"
                    class="sr-only"
                  >Shown rotated 180 degrees: with this combination of page orientation and flip
                    edge, the back of the sheet ends up upside down relative to the front.</span>
                </div>
              </div>

              <preview-status-message v-else>
                Update the preview to see this job.
              </preview-status-message>
            </div>

            <p-button
              v-if="hasNextUnit"
              aria-label="Next page"
              severity="secondary"
              rounded
              raised
              class="shrink-0"
              @click="goNextUnit"
            >
              <svg
                viewBox="0 0 20 20"
                fill="none"
                class="size-5"
              ><path
                d="M8 4l6 6-6 6"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
                stroke-linejoin="round"
              /></svg>
            </p-button>
          </template>
        </div>

        <!-- Thumbnail strip -->
        <div
          v-if="units.length > 1"
          class="flex shrink-0 items-center gap-1 border-t border-surface bg-surface-0 px-1 py-2"
        >
          <p-button
            aria-label="Scroll thumbnails left"
            severity="secondary"
            variant="text"
            rounded
            size="small"
            class="shrink-0"
            @click="scrollThumbnails(-1)"
          >
            <svg
              viewBox="0 0 20 20"
              fill="none"
              class="size-4"
            ><path
              d="M12 4l-6 6 6 6"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
              stroke-linejoin="round"
            /></svg>
          </p-button>

          <div
            ref="thumbnailStripRef"
            class="flex grow snap-x snap-mandatory gap-3 overflow-x-auto scroll-smooth px-1"
          >
            <div
              v-for="(unit, index) in units"
              :key="unit.pages[0]!.number"
              class="flex shrink-0 snap-start flex-col items-center gap-1"
            >
              <span
                v-if="isBooklet"
                class="text-[0.65rem] font-medium text-muted-color"
              >Folded booklet — sheet {{ index + 1 }}</span>
              <div class="flex gap-1.5">
                <preview-thumbnail
                  v-for="(page, pageIndex) in unit.pages"
                  :key="page.number"
                  :page="page"
                  :side="isPaired ? (pageIndex === 0 ? 'front' : 'back') : null"
                  :selected="index === selectedUnitIndex"
                  :rotated="!isBooklet && pageIndex === 1 && isUnitBackRotated(unit)"
                  @click="selectUnitIndex(index)"
                />
              </div>
            </div>
          </div>

          <p-button
            aria-label="Scroll thumbnails right"
            severity="secondary"
            variant="text"
            rounded
            size="small"
            class="shrink-0"
            @click="scrollThumbnails(1)"
          >
            <svg
              viewBox="0 0 20 20"
              fill="none"
              class="size-4"
            ><path
              d="M8 4l6 6-6 6"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
              stroke-linejoin="round"
            /></svg>
          </p-button>
        </div>

        <!-- Footer -->
        <div class="flex shrink-0 flex-wrap items-center justify-end gap-2 border-t border-surface px-4 py-3">
          <p-button
            label="Close"
            severity="secondary"
            variant="text"
            @click="preview.close()"
          />
          <p-button
            label="Print"
            severity="primary"
            :loading="jobCreator.printLoading"
            @click="onPrintClick"
          />
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
type Unit = { pages: PrintPreviewPage[] };

const props = defineProps<{
  jobCreator: ReturnType<typeof useJobCreator>;
  preview: ReturnType<typeof usePrintPreview>;
}>();

const isBooklet = computed(() => props.jobCreator.impositionTemplate === 'booklet');

// A booklet always pairs pages up regardless of the two-sided setting.
const isPaired = computed(() => isBooklet.value || props.jobCreator.duplexMode !== 'disabled');

const duplexAxis = computed<'long' | 'short' | null>(() => {
  if (isBooklet.value) return null;
  if (props.jobCreator.duplexMode === 'duplex-long-edge') return 'long';
  if (props.jobCreator.duplexMode === 'duplex-short-edge') return 'short';
  return null;
});

// front and back sit side by side, so a long-edge flip on
// a portrait page (or short-edge on landscape) already lines up and needs no rotation.
const isUnitBackRotated = (unit: Unit): boolean => {
  if (duplexAxis.value === null || isBooklet.value) return false;
  const front = unit.pages[0];
  if (!front) return false;
  const isLandscape = front.width > front.height;
  return (isLandscape && duplexAxis.value === 'long') || (!isLandscape && duplexAxis.value === 'short');
};

const rotateBack180 = computed(() => selectedUnit.value !== null && isUnitBackRotated(selectedUnit.value));

// Groups the flat page list into units: one page each, or a front/back pair when isPaired
const units = computed<Unit[]>(() => {
  const pages = [...props.preview.pages].sort((a, b) => a.number - b.number);
  if (!isPaired.value) return pages.map(page => ({ pages: [page] }));
  const result: Unit[] = [];
  for (let i = 0; i < pages.length; i += 2) {
    result.push({ pages: pages.slice(i, i + 2) });
  }
  return result;
});

const selectedUnitIndex = computed(() => {
  const currentNumber = props.preview.selectedPage?.number;
  if (currentNumber === undefined) return 0;
  const index = units.value.findIndex(unit => unit.pages.some(page => page.number === currentNumber));
  return index === -1 ? 0 : index;
});

const selectedUnit = computed<Unit | null>(() => units.value[selectedUnitIndex.value] ?? null);

const hasPrevUnit = computed(() => selectedUnitIndex.value > 0);
const hasNextUnit = computed(() => selectedUnitIndex.value < units.value.length - 1);

const selectUnitIndex = (index: number) => {
  const unit = units.value[index];
  if (unit) props.preview.selectPage(unit.pages[0]!.number);
};
const goPrevUnit = () => selectUnitIndex(selectedUnitIndex.value - 1);
const goNextUnit = () => selectUnitIndex(selectedUnitIndex.value + 1);

const unitPositionLabel = computed(() => {
  const total = units.value.length;
  if (total === 0) return null;
  const position = selectedUnitIndex.value + 1;
  return isPaired.value
    ? `Sheet ${position} of ${total}`
    : `Page ${position} of ${total}`;
});

const thumbnailStripRef = ref<HTMLElement | null>(null);
const scrollThumbnails = (direction: -1 | 1) => {
  thumbnailStripRef.value?.scrollBy({ left: direction * 180, behavior: 'smooth' });
};

const onPrintClick = async () => {
  await props.jobCreator.print();
  props.preview.close();
};

const dialogRef = ref<HTMLElement | null>(null);
watch(() => props.preview.visible, (visible) => {
  if (visible) nextTick(() => dialogRef.value?.focus());
});
</script>
