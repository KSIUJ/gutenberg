<template>
  <div v-if="artefacts">
    <v-list flat class="mx-3">
      <v-list-item v-for="arx in artefacts" :key="arx.name">
        <v-list-item-icon>
          <v-icon>upload_file</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ arx.name }}</v-list-item-title>
        </v-list-item-content>
        <v-list-item-action>
          <v-progress-circular v-if="arx.progress > 0 && arx.progress < 100"
                               size="36" rotate="270" :value="arx.progress" color="primary">
          </v-progress-circular>
          <v-icon v-if="arx.progress === 100" color="green" large>check</v-icon>
        </v-list-item-action>
      </v-list-item>
    </v-list>
  </div>
</template>

<script>
import { API } from '@/common/api';

export default {
  name: 'ArtefactUploader',
  data() {
    return {
      artefacts: [],
    };
  },
  props: ['jobId'],
  mounted() {
    this.artefacts = this.$store.state.files.map((val) => ({
      file: val,
      name: val.name,
      progress: 0,
    }));
    if (this.artefacts.length > 0) {
      this.uploadArtefact(0);
    }
  },
  methods: {
    uploadArtefact(idx) {
      const formData = new FormData();
      formData.append('file', this.artefacts[idx].file);
      if (idx + 1 === this.artefacts.length) {
        formData.append('last', true);
      }
      window.axios.post(`${API.jobs + this.jobId + API.upload}/?format=json`, formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            this.artefacts[idx].progress = Math.floor((progressEvent.loaded
              / progressEvent.total) * 100);
          },
        }).then(() => {
        if (idx < this.artefacts.length - 1) {
          this.uploadArtefact(idx + 1);
        } else {
          this.$store.commit('setFiles', []);
        }
      });
    },
  },
};
</script>

<style scoped>

</style>
