<template>
  <v-card>
    <v-card-title>IPP Settings</v-card-title>
    <v-card-subtitle>You can print directly from your device using IPP</v-card-subtitle>

    <v-card-text>
      <v-text-field disabled
                    :value="printer.name"
                    label="Printer" prepend-icon="print"></v-text-field>
      <p class="text-h6">Authenticate using secret URI.</p>
      <p>Recommended for: Android, Linux (CUPS), MacOSX (CUPS).</p>
      <v-text-field @click="$event.target.select()" readonly
                    :value="ippTokenUrl"
                    label="Your personal IPP endpoint for this printer"
                    hint="Do not share this with others - all files printed using this address will be accounted to your quota."
                    persistent-hint class="mb-3" prepend-icon="link"></v-text-field>
      <p class="text-h6">Authenticate with username and token/password.</p>

      <p>Recommended for: Windows, IOS (with Bonjour server).</p>
      <v-text-field @click="$event.target.select()" readonly
                    :value="ippAuthUrl"
                    label="Alternative IPP endpoint with HTTP-basic authentication for this printer"
                    hint="You will be required to authenticate using your username and token/ipp password to print using this endpoint."
                    persistent-hint class="mb-3" prepend-icon="link"></v-text-field>
      <v-text-field @click="$event.target.select()" readonly
                    :value="user.username"
                    label="Your username" prepend-icon="person"></v-text-field>
      <v-text-field @click="$event.target.select()" readonly
                    :value="user.api_key"
                    label="Your IPP token/passwordr"
                    hint="Do not share this with others."
                    persistent-hint prepend-icon="vpn_key" class="mb-3"></v-text-field>
      <p>You can re-generate your IPP token/password if accidentally shared it with others. Please remember that you
        will have to update it in any device you have set up Gutenberg IPP with.</p>
    </v-card-text>

    <v-divider></v-divider>

    <v-card-actions>
      <v-dialog
        v-model="dialog"
        width="500"
      >
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            color="error"
            text
            v-bind="attrs"
            v-on="on"
          >Reset IPP token
          </v-btn>
        </template>

        <v-card>
          <v-card-title>
            Reset IPP token
          </v-card-title>
          <v-card-text>
            Are you sure you want to reset your IPP token/password? You will need to update all of your connected
            devices with the new token and/or secret ipp uri.
          </v-card-text>
          <v-divider></v-divider>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              text
              @click="dialog = false"
            >
              Cancel
            </v-btn>
            <v-btn color="error" text @click="resetApiToken" :loading="requestingReset">
              Reset
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        text
        @click="$emit('close')"
      >Close
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import {API} from "../common/api";
import {getCsrfToken} from "../common/utils";

export default {
  data() {
    return {
      requestingReset: false,
      dialog: false,
      getCsrfToken,
    }
  },
  name: "PrinterIPPSettings",
  props: ['printer'],
  methods: {
    getIppUrl(auth, printer_id) {
      const proto = window.location.protocol === 'https:' ? 'ipps://' : 'ipp://';
      const port = window.location.port === '' ?
        (window.location.protocol === 'https:' ? '443' : '80') : window.location.port;
      return proto + window.location.hostname + ':' + port + API.ipp + auth + '/' + printer_id + '/print';
    },
    resetApiToken() {
      this.requestingReset = true;
      axios.post(API.resetToken).then((res) => {
        window.location.reload();
      });
    },
  },
  computed: {
    user: {
      get() {
        return this.$store.state.user
      }
    },
    ippAuthUrl() {
      return this.getIppUrl('basic', this.printer.id);
    },
    ippTokenUrl() {
      return this.getIppUrl(this.user.api_key, this.printer.id);
    },
  }
}
</script>

<style scoped>

</style>
