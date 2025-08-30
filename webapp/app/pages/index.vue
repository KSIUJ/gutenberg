<template>
  <sidebar-layout>
    <template #sidebar>
      <app-panel
        v-if="$auth.me.value === Unauthenticated"
        ghost
        class="grow"
      >
        <div class="flex grow flex-col items-center justify-center space-y-4 text-center">
          <div>
            Sign in to print documents online
          </div>
          <sign-in-button size="large" />
        </div>
      </app-panel>

      <div
        v-else
        class="flex grow flex-col space-y-4"
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
          A <b class="text-primary">reliable</b> office printing gateway.
        </p>

        <h1 class="mt-8 text-header">
          Print directly from your device
        </h1>
        <p>
          Gutenberg supports the <b class="text-primary">Internet Printing Protocol</b>.
          You can connect to this printer in your device settings
          <b class="text-primary">without having to install dedicated printer drivers</b>
          and start print jobs from apps on your device,
          <b class="text-primary">from any network</b> with internet access.
        </p>

        <p-button
          v-slot="slotProps"
          severity="primary"
          as-child
          fluid
        >
          <NuxtLink
            v-bind="slotProps"
            to="/print/setup-ipp/"
          >
            Setup native printing
          </NuxtLink>
        </p-button>

        <h1 class="mt-8 text-header">
          About the Gutenberg project
        </h1>
        <p>
          Gutenberg is an <b class="text-primary">open-source</b>
          project created and maintained by the people at
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

        <p class="mt-8 text-center text-xs text-balance">
          &copy; 2015&ndash;{{ buildYear }}
          <a
            class="text-link"
            href="https://ksi.ii.uj.edu.pl/"
          >KSI&nbsp;UJ</a><br>

          Gutenberg is released under the
          <a
            class="text-link"
            href="https://github.com/KSIUJ/gutenberg/blob/master/LICENSE"
          >GNU Affero General Public License v3.0</a>
        </p>
      </app-content>
    </template>
  </sidebar-layout>
</template>

<script setup lang="ts">
import ksiPoweredByLogo from '~/assets/img/powered-by-ksi.svg';
import githubLogo from '~/assets/img/github-mark.svg';

const { $auth } = useNuxtApp();
const runtimeConfig = useRuntimeConfig();

const buildYear = new Date(runtimeConfig.public.buildDate).getFullYear();
</script>
