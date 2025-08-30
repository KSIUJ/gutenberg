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
        <big-link
          href="https://ksi.ii.uj.edu.pl/"
          :img-src="ksiPoweredByLogo"
          alt="&quot;Powered by KSI&quot; logo"
        >
          <b class="text-primary">Computer Science Students' Association</b><br>
          at <b class="text-primary">Jagiellonian University</b>, Krakow, Poland
        </big-link>
        <p>
          The project's source&nbsp;code is hosted on GitHub.
          The&nbsp;GitHub repository is also the place to report issues and submit feature requests.
        </p>
        <big-link
          label="KSIUJ/gutenberg"
          href="https://github.com/KSIUJ/gutenberg/"
          :img-src="githubLogo"
          img-alt="GitHub logo"
        />
        <p>
          Gutenberg is <b class="text-primary">self-hosted</b>, you can deploy it in your organization.
          Check out Gutenberg's documentation for more information.
        </p>
        <big-link
          label="Online documentation"
          href="https://ksiuj.github.io/gutenberg/"
        />
      </app-content>
    </template>
  </sidebar-layout>
</template>

<script setup lang="ts">
import ksiPoweredByLogo from '~/assets/img/powered-by-ksi.svg';
import githubLogo from '~/assets/img/github-mark.svg';

const { $auth } = useNuxtApp();
</script>
