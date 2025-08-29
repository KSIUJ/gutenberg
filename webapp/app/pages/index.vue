<template>
  <sidebar-layout>
    <template #sidebar>
      <app-panel
        v-if="$auth.me.value === Unauthenticated"
        ghost
        class="grow"
      >
        <div class="grow flex flex-col items-center justify-center text-center space-y-4">
          <div>
            Sign in to print documents online
          </div>
          <sign-in-button size="large" />
        </div>
      </app-panel>

      <div
        v-else
        class="space-y-4 flex flex-col grow"
      >
        <print-options />

        <!--        <app-panel header="Recently printed" class="grow"> -->
        <!--          <div class="text-muted-color text-center p-6">This feature is not yet implemented</div> -->
        <!--        </app-panel> -->
      </div>
    </template>

    <template #content>
      <app-content class="space-y-4">
        <h1 class="text-header">
          Welcome to Gutenberg
        </h1>
        <p class="my-4">
          A <span class="text-primary">reliable</span> office printing gateway
        </p>

        <h1 class="text-header">
          Print directly from your device
        </h1>
        <p>
          Gutenberg supports printing using the <b class="text-emphasis-color">Internet Printing Protocol</b>
          <p-button
            v-slot="slotProps"
            variant="outlined"
            severity="primary"
            as-child
          >
            <NuxtLink
              v-bind="slotProps"
              to="/print/setup-ipp/"
            >
              Learn more
            </NuxtLink>
          </p-button>
        </p>

        <p>
          Gutenberg is an <b class="text-primary">open-source</b>
          project created and maintained by
          <b class="text-primary">KSI&nbsp;UJ</b>:
        </p>
        <a
          href="https://ksi.ii.uj.edu.pl/"
          class="border rounded-border border-surface bg-surface-50 hover:bg-surface-0 transition-colors flex flex-row p-4 gap-4 items-center"
        >
          <img
            src="~/assets/img/powered-by-ksi.svg"
            alt="Powered by KSI logo"
            class="h-16 w-auto shrink-0"
          >

          <div class="grow text-center">
            <b class="text-primary">Computer Science Students' Association</b><br>
            at <b class="text-primary">Jagiellonian University</b>, Krakow, Poland
          </div>
        </a>
        <p>
          The project's source&nbsp;code is hosted on GitHub.
          The&nbsp;GitHub repository is also the place to report issues and submit feature requests.
        </p>
        <a
          href="https://github.com/KSIUJ/gutenberg/"
          class="border rounded-border border-surface bg-surface-50 hover:bg-surface-0 transition-colors flex flex-row p-4 gap-4 items-center"
        >
          <img
            src="~/assets/img/github-mark.svg"
            alt="GitHub logo"
            class="h-8 w-auto shrink-0"
          >

          <div class="grow text-center text-primary font-semibold">
            KSIUJ/gutenberg
          </div>
        </a>
        <p>
          Gutenberg is <b class="text-primary">self-hosted</b>, you can deploy it in your organization.
          Check out Gutenberg's documentation for more information.
        </p>
        <a
          href="https://ksiuj.github.io/gutenberg/"
          class="border rounded-border border-surface bg-surface-50 hover:bg-surface-0 transition-colors flex flex-row p-4 gap-4 items-center"
        >
          <div class="grow text-center text-primary font-semibold">
            Online documentation
          </div>
        </a>
      </app-content>
    </template>
  </sidebar-layout>
</template>

<script setup lang="ts">
const { $auth } = useNuxtApp();
</script>
