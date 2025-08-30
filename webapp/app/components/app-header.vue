<template>
  <header class="fixed top-0 left-0 right-0 block h-(--header-height) bg-surface-50 border-b border-surface z-10 shadow-xs">
    <div class="px-4 h-full mx-auto max-w-5xl flex flex-row items-center justify-between">
      <NuxtLink
        to="/"
        class="flex flex-row items-center h-full gap-2"
      >
        <div class="py-2 h-full">
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
        <p-button
          variant="text"
          :label="$auth.me.value.username"
          aria-haspopup="menu"
          aria-controls="user_menu"
          @click="toggleUserMenu"
        />
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
const { $csrfToken, $auth } = useNuxtApp();
const { logoutEndpoint } = useApiRepository();
const route = useRoute();

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
