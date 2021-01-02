<template>
  <div>
    <div v-if="job === null" class="text-center mt-10">
      <v-progress-circular indeterminate size="70" width="5" color="primary"></v-progress-circular>
    </div>
    <div v-if="job !== null">
      <v-card class="mb-5">
        <v-card-title>Job status</v-card-title>
        <v-stepper v-if="stage > 0" vertical :value="stage" class="elevation-0 pb-2">
          <v-stepper-step step="1" :complete="stage > 1">
            Job created
          </v-stepper-step>
          <v-stepper-content step="1">
            <p class="">Gutenberg has registered the printing request
              and is now waiting for a document to print.</p>
            <v-progress-linear :indeterminate="update"></v-progress-linear>
          </v-stepper-content>
          <v-stepper-step step="2" :complete="stage > 2">
            Pending
          </v-stepper-step>
          <v-stepper-content step="2">
            <p class="">Gutenberg has received all required information
              and should start processing the request shortly.</p>
            <v-progress-linear :indeterminate="update"></v-progress-linear>
          </v-stepper-content>
          <v-stepper-step step="3" :complete="stage > 3">
            Processing
          </v-stepper-step>
          <v-stepper-content step="3">
            <p class="">Gutenberg is processing the request,
              it might take up to 30 seconds to complete.</p>
            <v-progress-linear :indeterminate="update"></v-progress-linear>
          </v-stepper-content>
          <v-stepper-step step="4" :complete="stage > 4">
            Printing
          </v-stepper-step>
          <v-stepper-content step="4">
            <p class="">The request has been sent to the printer.</p>
            <v-progress-linear :indeterminate="update"></v-progress-linear>
          </v-stepper-content>
          <v-stepper-step step="5" :complete="stage === 5">
            Completed
          </v-stepper-step>
          <v-stepper-content step="5">
            <v-alert type="success">
              Your document is ready or will finish printing soon.
              Thank you for using Gutenberg.
            </v-alert>
          </v-stepper-content>
        </v-stepper>
        <v-card-text v-if="stage === -3">
          <v-alert type="error">
            Gutenberg has encountered an error. See details bellow.
          </v-alert>
        </v-card-text>
        <v-card-text v-if="stage === -2">
          <v-alert type="info">
            This job has been cancelled.
          </v-alert>
        </v-card-text>
        <v-card-text v-if="stage === -1">
          <v-alert type="warning">
            Cancellation request received. Depending on the stage some
            or all pages might still be printed.
          </v-alert>
          <v-progress-linear :indeterminate="update"></v-progress-linear>
        </v-card-text>
        <v-card-text v-if="stage < -100">
          <v-alert type="error">
            Unknown job status.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn v-if="cancellable"
                 color="error" text @click="cancelJob"
          >Cancel job
          </v-btn>
          <v-btn v-if="!update" color="primary" text large to="/">
            Back to main page
          </v-btn>
        </v-card-actions>
      </v-card>

      <v-card>
        <v-card-title>Job details</v-card-title>
        <v-card-text>
          <v-text-field label="Printer" prepend-icon="print" :value="job.printer"
                        outlined readonly></v-text-field>
          <v-text-field v-if="job.pages" label="Pages" prepend-icon="library_books"
                        :value="job.pages" outlined readonly></v-text-field>
          <v-textarea v-if="job.status_reason" label="Status reason" outlined readonly
                      prepend-icon="info" :value="job.status_reason" no-resize></v-textarea>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script>
import { API } from '../common/api';

export default {
  name: 'JobStatus',
  data() {
    return {
      update: true,
      job: null,
      stage: 0,
      cancellable: false,
    };
  },
  methods: {
    updateStatus() {
      window.axios.get(`${API.jobs + this.jobId}/?format=json`).then((resp) => {
        this.job = resp.data;
        this.stage = this.jobStage();
        this.update = !(this.stage < -1 || this.stage === 5);
        this.cancellable = this.stage > 0 && this.stage !== 5;
        if (this.update) {
          this.timerId = setTimeout(this.updateStatus, 500);
        }
      });
    },
    jobStage() {
      const stage = {
        INCOMING: 1,
        PENDING: 2,
        PROCESSING: 3,
        PRINTING: 4,
        COMPLETED: 5,
        CANCELING: -1,
        CANCELED: -2,
        ERROR: -3,
      }[this.job.status];
      if (stage) {
        return stage;
      }
      return -9999;
    },
    cancelJob() {
      window.axios.post(`${API.jobs + this.jobId + API.cancelJob}/?format=json`);
    },
  },
  mounted() {
    this.updateStatus();
  },
  computed: {
    jobId() {
      return this.$route.params.id;
    },
  },
};
</script>
