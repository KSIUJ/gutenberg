<template>
  <single-column-layout>
    <app-panel
      header="Setup IPP"
    >
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
          You can print directly from your device using IPP
        </p>

        <p-float-label variant="in">
          <p-select
            id="printer-select"
            v-model="selectedPrinterId"
            :options="printers.data.value"
            option-value="id"
            option-label="name"
            fluid
            :loading="printers.pending.value"
          />
          <label for="printer-select">Printer</label>
        </p-float-label>

        <template v-if="details !== null">
          <p-fieldset legend="Authenticate with username and token/password">
            <p class="mb-4">
              Recommended for: Windows, iOS (with Bonjour server).
            </p>
            <p-ifta-label>
              <p-input-text
                id="ipp-basic-auth-url"
                readonly
                :value="details.ippBasicAuthUrl"
                fluid
                aria-labelledby="ipp-basic-auth-url-description"
                @click="$event.target.select()"
              />
              <label for="ipp-basic-auth-url">
                IPP endpoint with HTTP-basic authentication for this printer
              </label>
            </p-ifta-label>
            <input-hint
              id="ipp-basic-auth-url-description"
              class="mb-4"
            >
              You will be asked to authenticate using your username and IPP token/password to print
              using this endpoint.
            </input-hint>

            <div class="flex flex-col lg:flex-row gap-4">
              <div class="grow">
                <p-ifta-label>
                  <p-input-text
                    id="ipp-username"
                    readonly
                    :value="details.ippUsername"
                    fluid
                    @click="$event.target.select()"
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
                    @click="$event.target.select()"
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
          </p-fieldset>

          <p-fieldset legend="Authenticate using secret URI">
            <p class="mb-4">
              Recommended for: Linux (CUPS), macOS (CUPS), Android.
            </p>
            <p-ifta-label>
              <p-input-text
                id="ipp-token-url"
                readonly
                :value="details.ippTokenUrl"
                fluid
                aria-labelledby="ipp-token-url-description"
                @click="$event.target.select()"
              />
              <label for="ipp-token-url">Your personal IPP endpoint for this printer</label>
            </p-ifta-label>
            <input-hint
              id="ipp-token-url-description"
              warn
            >
              Do not share this with others - all files printed using this address
              will be accounted to your quota.
            </input-hint>
          </p-fieldset>

          <p-fieldset legend="Reset IPP token/password">
            <div class="flex flex-col lg:flex-row lg:items-center gap-4">
              <p class="text-sm grow">
                You can re-generate your IPP token/password if accidentally shared it with others.<br>
                Please remember that you will have to update it in any device you have set up
                Gutenberg IPP with.
              </p>

              <!-- TODO: Verify the accessibility of this dialog -->
              <p-button
                label="Reset IPP token"
                severity="danger"
                variant="outlined"
                class="self-end lg:self-auto shrink-0"
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
import { API } from '../../../../webapp_old/src/common/api';

const { $auth } = useNuxtApp();
const confirm = useConfirm();
const toast = useToast();

const printers = await usePrinters();

const printersErrorMessage = computed(() => {
  if (printers.error.value === undefined) return null;
  return getErrorMessage(printers.error.value) ?? 'Failed to load printer list';
});

// TODO: Extract the printer picker as a common component/composable
const getFirstPrinterId = () => {
  return printers.data.value?.at(0)?.id ?? null;
};

const selectedPrinterId = ref(getFirstPrinterId());

const details = computed(() => {
  if ($auth.me.value === Unauthenticated) return null;
  if (selectedPrinterId.value === null) return null;
  if (!printers.data.value) return null;

  const printer = printers.data.value.find(printer => printer.id === selectedPrinterId.value);
  if (!printer) return null;

  const createIppUrl = (authField: string) => {
    const useHttps = window.location.protocol === 'https:';
    const [proto, defaultPort] = useHttps ? ['ipps://', '443'] : ['ipp://', '80'];
    const port = window.location.port || defaultPort;
    return `${proto}${window.location.hostname}:${port}${API.ipp}${authField}/${selectedPrinterId.value}/print`;
  };
  return {
    ippTokenUrl: createIppUrl($auth.me.value.api_key),
    ippBasicAuthUrl: createIppUrl('basic'),
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

definePageMeta({
  middleware: [
    'require-auth',
  ],
});
</script>
