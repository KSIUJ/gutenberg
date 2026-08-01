<template>
  <n-modal v-model:show="visible" title="Podgląd wydruku" size="xl">
    <div v-if="loading">Ładowanie podglądu…</div>
    <div v-else>
      <div v-if="status === 'READY' && pages.length">
        <img :src="pages[current]" alt="preview" style="max-width:100%; max-height:70vh; display:block; margin:0 auto;" />
        <div class="mt-2 flex items-center justify-center gap-2">
          <button @click="prev" :disabled="current===0">Prev</button>
          <span>{{current+1}} / {{pages.length}}</span>
          <button @click="next" :disabled="current+1===pages.length">Next</button>
          <button @click="print" class="primary">Drukuj</button>
          <button @click="regenerate">Regeneruj</button>
          <button @click="close">Zamknij</button>
        </div>
      </div>
      <div v-else-if="status === 'PROCESSING'">Generowanie podglądu…</div>
      <div v-else-if="status === 'FAILED'">Generowanie podglądu nie powiodło się.</div>
      <div v-else>Brak podglądu</div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { createApiRepository } from '~/utils/api-repository';

const props = defineProps<{ jobId: number, visible: boolean }>();
const emit = defineEmits(['update:visible']);

const api = createApiRepository(fetch); // lub sposób w twoim projekcie
const visible = ref(props.visible);
const status = ref<string | null>(null);
const pages = ref<string[]>([]);
const current = ref(0);
const loading = ref(true);

const fetchPreview = async () => {
  loading.value = true;
  try {
    const res = await api.getPreview(props.jobId);
    status.value = (res as any).status;
    pages.value = (res as any).pages || [];
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
    if (status.value === 'PROCESSING') setTimeout(fetchPreview, 2000);
  }
};

const prev = () => { if (current.value>0) current.value--; };
const next = () => { if (current.value+1 < pages.value.length) current.value++; };
const regenerate = async () => { await api.regeneratePreview(props.jobId); fetchPreview(); };
const print = async () => { await api.sendFromPreview(props.jobId); alert('Wysłano do drukarki'); };
const close = () => { emit('update:visible', false); };

onMounted(fetchPreview);
</script>
