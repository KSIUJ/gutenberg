<template>
  <header class="block h-(--header-height) border-b border-surface bg-surface-50 shadow-xs y-md:fixed y-md:top-0 y-md:right-0 y-md:left-0 y-md:z-10">
    <div class="mx-auto flex h-full max-w-5xl flex-row items-center justify-between px-4">
      <NuxtLink
        to="/"
        class="flex h-full flex-row items-center gap-2"
      >
        <div class="h-full py-2">
          <img
            alt=""
            src="~/assets/img/gutenberg-logo-120.png"
            class="h-full w-auto"
          >
        </div>

        <div class="text-lg font-semibold">
          Gutenberg
        </div>
      </NuxtLink>

      <template v-if="$auth.me.value === Unauthenticated">
        <sign-in-button
          v-if="!route.meta.hideSignInButton"
          variant="text"
        />
      </template>
      <template v-else>
        <div class="flex items-center gap-2">
          <p-button
            variant="text"
            :label="$auth.me.value.username"
            aria-haspopup="menu"
            aria-controls="user_menu"
            @click="toggleUserMenu"
          />
          <div
            class="group relative"
            tabindex="0"
            aria-describedby="quota-summary"
          >
            <p-tag
              :value="quotaLabel"
              :severity="quotaSeverity"
              rounded
            />
            <div
              id="quota-summary"
              role="tooltip"
              class="pointer-events-none absolute top-full right-0 z-20 mt-2 hidden w-72 rounded-lg border border-surface-200 bg-surface-0 p-3 shadow-lg group-hover:block group-focus-within:block"
            >
              <div class="mb-2 flex items-baseline justify-between gap-3">
                <span class="font-semibold">Print quota</span>
                <span class="text-xs text-muted-color">Printed pages</span>
              </div>
              <p
                v-if="quotaPeriods.length === 0"
                class="text-sm text-muted-color"
              >
                No page limit applies to your account.
              </p>
              <dl
                v-else
                class="space-y-2"
              >
                <div
                  v-for="quota in quotaPeriods"
                  :key="quota.period"
                  class="flex items-center justify-between gap-4 border-t border-surface-100 pt-2 first:border-t-0 first:pt-0"
                >
                  <dt class="text-sm font-medium">
                    {{ quotaPeriodLabels[quota.period] }}
                  </dt>
                  <dd class="text-right text-sm">
                    <span class="font-medium">{{ quota.remaining_pages }} remaining</span>
                    <span class="block text-xs text-muted-color">{{ quota.used_pages }} of {{ quota.limit_pages }} used</span>
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
        <p-menu
          id="user_menu"
          ref="user-menu"
          :popup="true"
          :model="userMenuItems"
        />
      </template>
    </div>
    <form
      ref="logout-form"
      :action="logoutEndpoint"
      method="post"
    >
      <input
        type="hidden"
        name="csrfmiddlewaretoken"
        :value="$csrfToken"
      >
    </form>
  </header>
</template>

<script setup lang="ts">
import { useIntervalFn } from '@vueuse/core';

const { $csrfToken, $auth } = useNuxtApp();
const { logoutEndpoint } = useApiRepository();
const route = useRoute();

const quotaPeriods = computed(() => {
  if ($auth.me.value === Unauthenticated) return [];
  return $auth.me.value.quota;
});

const remainingPages = computed(() => Math.min(
  ...quotaPeriods.value.map(quota => quota.remaining_pages),
));

const quotaLabel = computed(() => {
  if (quotaPeriods.value.length === 0) return 'Unlimited pages';
  return `${remainingPages.value} pages available`;
});

const quotaSeverity = computed(() => {
  if (quotaPeriods.value.length === 0) return 'secondary';
  if (remainingPages.value === 0) return 'danger';
  const smallestLimit = Math.min(...quotaPeriods.value.map(quota => quota.limit_pages));
  return remainingPages.value / smallestLimit <= 0.1 ? 'warn' : 'secondary';
});

const quotaPeriodLabels = {
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
};

useIntervalFn(() => {
  if (quotaPeriods.value.length === 0) return;
  $auth.refreshMe().catch();
}, 5000);

const userMenuItems = computed(() => {
  if ($auth.me.value === Unauthenticated) {
    return [];
  }
  const adminItems = $auth.me.value.is_staff
    ? [
        {
          label: 'Admin settings',
          url: '/admin/',
        },
      ]
    : [];
  return [
    ...adminItems,
    {
      label: 'Sign out',
      command: () => {
        logoutForm.value?.submit();
      },
    },
  ];
});

const logoutForm = useTemplateRef('logout-form');

const userMenu = useTemplateRef('user-menu');
const toggleUserMenu = (event: MouseEvent) => {
  userMenu.value?.toggle(event);
};
</script>
