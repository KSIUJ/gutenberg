<template>
  <div>
    <h1 class="text-h2 mb-4">Print</h1>

    <v-form ref="form">

      <h4 class="text-h4 mb-3">Select printer</h4>
      <v-select label="Printer" outlined :items="printers" item-text="name" :item-value="i=>i"
                @change="printerSelected" required prepend-icon="print" :loading="loading_printers"
                :disabled="loading_printers">
        <template v-slot:item="data">
          <v-badge
            inline
            color="success"
            :content="printerBadgeText(data.item)"
            :value="printerBadgeText(data.item)"
          >
            {{ data.item.name }}
          </v-badge>
        </template>
      </v-select>

      <v-row>
        <v-col sm="12" md="8">
          <h4 class="text-h4 mb-3">Upload file</h4>

          <v-file-input outlined label="File to print" v-model="file" :disabled="!printer_id"
                        required :rules="validateFileRequired">
          </v-file-input>
        </v-col>
        <v-col>
          <h4 class="text-h4 mb-3">or print using IPP</h4>
          <p>Print directly from your device through system printing using the
            Internet Printing Protocol.</p>
          <v-btn color="info" large :disabled="!printer_id" class="mb-2">
            Show IPP settings for this printer
          </v-btn>
        </v-col>
      </v-row>

      <h4 class="text-h4 mb-3">Printing settings</h4>
      <v-text-field outlined label="Number of copies" type="number" min="1" max="100"
                    v-model="copies" :disabled="!printer_id" required prepend-icon="content_copy"
                    :rules="validateCopies">
      </v-text-field>
      <v-text-field outlined label="Pages to print" hint="e.g. 1-4, 7, 13-21" persistent-hint
                    placeholder="all" type="text" v-model="pages_to_print" :disabled="!printer_id"
                    :pattern="PAGES_TO_PRINT_PATTERN" prepend-icon="filter_list"
                    :rules="validatePageFilter"></v-text-field>
      <v-radio-group row v-model="two_sides" :disabled="!duplex_available">
        <v-radio label="One-sided" value="OS"></v-radio>
        <v-radio label="Two-sided (long edge)" value="TL"></v-radio>
        <v-radio label="Two-sided (short edge)" value="TS"></v-radio>
      </v-radio-group>
      <v-switch label="Print in color" color="success" :disabled="!color_available"></v-switch>

      <v-btn large color="primary" v-model="color" :disabled="!printer_id" type="button"
             @click="submit">Print
      </v-btn>
    </v-form>
  </div>
</template>

<script>
// @ is an alias to /src

export default {
  name: 'Home',
  data() {
    return {
      loading_printers: true,
      printers: [],
      printer_id: null,
      two_sides: 'TL',
      color: false,
      pages_to_print: '',
      copies: 1,
      file: null,
      color_available: false,
      duplex_available: false,
      PAGES_TO_PRINT_PATTERN:
        String.raw`^\s*\d+(?:\s*-\s*\d+)?(\s*,\s*\d+(?:\s*-\s*\d+)?)*\s*$`,
    };
  },
  mounted() {
    window.axios.get('/api/printers/?format=json').then((value) => {
      this.printers = value.data;
      this.loading_printers = false;
    });
  },
  methods: {
    printerBadgeText(value) {
      const features = [];
      if (value.color_supported) {
        features.push('color');
      }
      if (value.duplex_supported) {
        features.push('duplex');
      }
      return features.join('+');
    },
    printerSelected(value) {
      this.printer_id = value.id;
      this.color_available = value.color_supported;
      this.duplex_available = value.duplex_supported;

      if (!this.color_available) {
        this.color = false;
      }
      if (!this.duplex_available) {
        this.two_sides = 'OS';
      } else {
        this.two_sides = 'TL';
      }
    },
    submit() {
      console.log(this.$refs.form);
      if (!this.$refs.form.validate()) {
        return;
      }
      const formData = new FormData();
      formData.append('printer', this.printer_id);
      formData.append('file', this.file);
      formData.append('copies', this.copies);
      formData.append('pages_to_print', this.pages_to_print);
      formData.append('two_sides', this.two_sides);
      formData.append('color', this.color);
      console.log(formData);
      window.axios.post('/api/jobs/submit/?format=json', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    },
  },
  computed: {
    validatePageFilter() {
      return [
        (val) => val === '' || val.match(this.PAGES_TO_PRINT_PATTERN)
          || 'Invalid page filter expression.',
      ];
    },
    validateFileRequired() {
      return [
        (val) => !!val || (val && !val.size < 1) || 'Add a file to print.',
      ];
    },
    validateCopies() {
      return [
        (val) => val > 0 || 'Minimum 1 copy required',
        (val) => val <= 100 || 'Max 100 copies allowed',
      ];
    },
  },
  components: {},
};
</script>
