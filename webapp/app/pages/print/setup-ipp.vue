<template>
  <single-column-layout>
    <app-panel header="Setup IPP">
      <template v-if="printers.data.value === undefined || printers.data.value.length === 0">
        <p-message
          v-if="printersErrorMessage !== null"
          severity="error"
        >
          {{ printersErrorMessage }}
        </p-message>
        <p-message
          v-else
          severity="info"
        >
          You do not have access to any printer
        </p-message>
      </template>
      <template v-else>
        <p class="mb-4">
          You can print directly from your device using IPP.
        </p>

        <p-float-label
          variant="in"
          class="mb-6"
        >
          <p-select
            id="printer-select"
            v-model="selectedPrinterId"
            :options="printerOptions"
            option-value="id"
            option-label="name"
            option-disabled="disabled"
            fluid
            :loading="printers.pending.value"
          >
            <template #option="{ option }">
              <div
                class="flex w-full items-center gap-2"
                :class="{ 'text-muted-color': option.disabled }"
              >
                <div>
                  <div>{{ option.name }}</div>
                  <div
                    v-if="option.disabled"
                    class="text-xs"
                  >
                    Under maintenance
                    <template v-if="option.maintenance_message">
                      — {{ option.maintenance_message }}
                    </template>
                  </div>
                </div>
              </div>
            </template>
          </p-select>
          <label for="printer-select">Printer</label>
        </p-float-label>
        <template v-if="details !== null">
          <!-- NEW UI SECTION: OS selection using PrimeVue buttons -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-surface-500 mb-3 uppercase tracking-wider">
              Select your Operating System
            </h3>
            <p-select-button
              v-model="selectedOS"
              :options="osOptions"
              option-label="label"
              option-value="id"
            />
          </div>
          <!-- DYNAMIC INSTRUCTIONS: Change depending on the selected operating system -->
          <p-fieldset
            :legend="`${activeOSLabel} Setup Guide`"
            class="mb-6"
          >
            <!-- INSTRUCTIONS FOR WINDOWS AND IOS (Require Basic Auth) -->
            <div
              v-if="selectedOS === 'windows' || selectedOS === 'ios'"
              class="flex flex-col gap-4"
            >
              <div class="mb-2 text-surface-700">
                <p
                  v-if="selectedOS === 'windows'"
                  class="mb-2"
                >
                  Follow these steps to add the printer on <strong>Windows 11</strong>:
                </p>
                <ol
                  v-if="selectedOS === 'windows'"
                  class="list-decimal list-inside space-y-1 mb-4 ml-1"
                >
                  <li>Open <strong>Settings</strong> > <strong>Bluetooth & devices</strong> > <strong>Printers & scanners</strong>.</li>
                  <li>Click <strong>Add device</strong> and then <strong>Add manually</strong>.</li>
                  <li>Choose <strong>Select a shared printer by name</strong>.</li>
                  <li>Paste the endpoint address below.</li>
                </ol>

                <p
                  v-if="selectedOS === 'ios'"
                  class="mb-4"
                >
                  <strong>Note:</strong> iOS printing usually requires a Bonjour server on your network to discover the printer automatically. Once discovered, you will use the credentials below.
                </p>
              </div>

              <!-- Text fields with Basic Authentication -->
              <p-ifta-label>
                <p-input-text
                  id="ipp-basic-auth-url"
                  readonly
                  :value="details.ippBasicAuthUrl"
                  fluid
                  aria-labelledby="ipp-basic-auth-url-description"
                  @click="handleFieldClick"
                />
                <label for="ipp-basic-auth-url">Printer IPP Endpoint</label>
              </p-ifta-label>
              <input-hint
                id="ipp-basic-auth-url-description"
                class="mb-4"
              >
                You will be asked to authenticate using your username and IPP token when connecting.
              </input-hint>

              <div class="flex flex-col gap-4 lg:flex-row">
                <div class="grow">
                  <p-ifta-label>
                    <p-input-text
                      id="ipp-username"
                      readonly
                      :value="details.ippUsername"
                      fluid
                      @click="handleFieldClick"
                    />
                    <label for="ipp-username">Your username</label>
                  </p-ifta-label>
                </div>
                <div class="grow">
                  <p-ifta-label>
                    <p-input-text
                      id="ipp-password"
                      readonly
                      :value="details.ippPassword"
                      fluid
                      aria-labelledby="ipp-password-description"
                      @click="handleFieldClick"
                    />
                    <label for="ipp-password">Your IPP token/password</label>
                  </p-ifta-label>
                  <input-hint
                    id="ipp-password-description"
                    warn
                  >
                    Do not share this with others.
                  </input-hint>
                </div>
              </div>
            </div>

            <!-- INSTRUCTIONS FOR MACOS, LINUX, AND ANDROID (Require Secret URI) -->
            <div
              v-if="selectedOS === 'macos' || selectedOS === 'linux' || selectedOS === 'android'"
              class="flex flex-col gap-4"
            >
              <div class="mb-2 text-surface-700">
                <p
                  v-if="selectedOS === 'macos'"
                  class="mb-4"
                >
                  Open <strong>System Settings > Printers & Scanners</strong>, click <strong>Add Printer</strong>, go to the <strong>IP</strong> tab, and use the Secret URI below. Set the protocol to IPP.
                </p>
                <!-- TODO: Verify the accessibility of this dialog -->
                <p
                  v-if="selectedOS === 'linux'"
                  class="mb-4"
                >
                  You can add this printer using the CUPS command line tool. (Tip: Avoid pasting secrets directly into interactive shell commands to keep them out of your shell history). Run a command similar to:<br>
                  <code class="block mt-2 p-2 bg-surface-100 rounded text-sm">lpadmin -p Gutenberg -v &lt;YOUR_SECRET_URI&gt; -E -m everywhere</code>
                </p>
                <p
                  v-if="selectedOS === 'android'"
                  class="mb-4"
                >
                  Use a 3rd party printing app (like CUPS Printing) and add the printer manually using your Secret URI below.
                </p>
              </div>

              <!-- Text field with Secret URI -->
              <p-ifta-label>
                <p-input-text
                  id="ipp-token-url"
                  readonly
                  :value="details.ippTokenUrl"
                  fluid
                  aria-labelledby="ipp-token-url-description"
                  @click="handleFieldClick"
                />
                <label for="ipp-token-url">Your personal IPP Secret URI</label>
              </p-ifta-label>
              <input-hint
                id="ipp-token-url-description"
                warn
              >
                Do not share this with others - all files printed using this address will be accounted to your quota.
              </input-hint>
            </div>
          </p-fieldset>

          <!-- DANGER ZONE SECTION: Resetting credentials -->
          <p-fieldset legend="Reset IPP token/password">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center">
              <p class="grow text-sm">
                You can re-generate your IPP token/password if accidentally shared it with others.<br>
                Please remember that you will have to update it in any device you have set up Gutenberg IPP with.
              </p>
              <p-button
                label="Reset IPP token"
                severity="danger"
                variant="outlined"
                class="shrink-0 self-end lg:self-auto"
                @click="resetToken"
              />
            </div>
          </p-fieldset>
        </template>
      </template>
    </app-panel>
  </single-column-layout>
</template>

<script setup lang="ts">
import { getIntQueryParam } from '~/utils/routing';
import { ref, computed, onMounted } from 'vue';

const apiRepository = useApiRepository();
const { $auth } = useNuxtApp();
const confirm = useConfirm();
const toast = useToast();
const route = useRoute();
const router = useRouter();

const printers = await usePrinters();

// Define options for operating system selection buttons
const osOptions = [
  { id: 'windows', label: 'Windows' },
  { id: 'macos', label: 'macOS' },
  { id: 'linux', label: 'Linux' },
  { id: 'ios', label: 'iOS' },
  { id: 'android', label: 'Android' },
];

// Default selection before detecting the user's OS
const selectedOS = ref('windows');

// Automatically detect the operating system based on User-Agent
onMounted(() => {
  const userAgent = navigator.userAgent.toLowerCase();
  if (userAgent.includes('win')) {
    selectedOS.value = 'windows';
  } else if (userAgent.includes('mac')) {
    if (userAgent.includes('iphone') || userAgent.includes('ipad')) {
      selectedOS.value = 'ios';
    } else {
      selectedOS.value = 'macos';
    }
  } else if (userAgent.includes('android')) {
    selectedOS.value = 'android';
  } else if (userAgent.includes('linux')) {
    selectedOS.value = 'linux';
  }
});

// Dynamic label for the fieldset header (e.g., "Windows Setup Guide")
const activeOSLabel = computed(() => {
  const os = osOptions.find(o => o.id === selectedOS.value);
  return os ? os.label : 'Device';
});

const printersErrorMessage = computed(() => {
  if (printers.error.value === undefined) return null;
  return getErrorMessage(printers.error.value) ?? 'Failed to load printer list';
});

const printerOptions = computed(() => (printers.data.value ?? []).map(printer => ({
  ...printer,
  disabled: !printer.is_available,
})));

const selectedPrinterId = computed<number | null>({
  get: () => getIntQueryParam(route.query.printer_id) ?? null,
  set: (value) => {
    router.replace({
      params: route.params,
      query: { ...route.query, printer_id: value ?? undefined },
      hash: route.hash,
    }).catch((error) => {
      console.error('Failed to update printer_id in route', error);
    });
  },
});

// Select the first available printer if none is selected, or if a bookmarked
// printer has entered maintenance since the link was created.
watchEffect(() => {
  if (!printers.data.value) return;
  const selectedPrinter = printers.data.value.find(printer => printer.id === selectedPrinterId.value);
  if (selectedPrinter?.is_available) return;
  const firstPrinter = printers.data.value.find(printer => printer.is_available);
  selectedPrinterId.value = firstPrinter?.id ?? null;
});

const details = computed(() => {
  if ($auth.me.value === Unauthenticated) return null;
  if (selectedPrinterId.value === null) return null;
  if (!printers.data.value) return null;

  const printer = printers.data.value.find(printer => printer.id === selectedPrinterId.value);
  if (!printer || !printer.is_available) return null;

  return {
    ippTokenUrl: apiRepository.createIppUri($auth.me.value.api_key, selectedPrinterId.value),
    ippBasicAuthUrl: apiRepository.createIppUri(null, selectedPrinterId.value),
    ippUsername: $auth.me.value.username,
    ippPassword: $auth.me.value.api_key,
  };
});

const resetToken = () => {
  confirm.require({
    header: 'Reset IPP token?',
    message: 'Are you sure you want to reset your IPP token/password? You will need to update all of your connected devices with the new token or secret IPP URI.',
    rejectLabel: 'Cancel',
    acceptLabel: 'Reset',
    accept: async () => {
      try {
        await $auth.resetIppToken();
      } catch (error) {
        console.error('Failed to reset token', error);
        toast.add({
          severity: 'error',
          summary: 'Failed to reset token',
          detail: getErrorMessage(error),
        });
      }
    },
  });
};

const handleFieldClick = (event: MouseEvent) => {
  if (event.target instanceof HTMLInputElement) event.target.select();
};

definePageMeta({
  middleware: [
    'require-auth',
  ],
});
</script>
