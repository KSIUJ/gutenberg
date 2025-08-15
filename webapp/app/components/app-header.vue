<template>
  <header class="fixed top-0 left-0 right-0 block h-(--header-height) bg-gray-800">
    <div class="px-4 h-full mx-auto max-w-5xl flex flex-row items-center justify-between">
      Gutenberg
      <Button v-if="$auth.me.value === Unauthenticated" label="Sign in" as="a" href="/login" variant="outlined" />
      <template v-else-if="$auth.me.value !== undefined">
        <Button variant="text" :label="$auth.me.value.username" aria-haspopup="menu" aria-controls="user_menu" @click="toggleUserMenu" />
        <Menu id="user_menu" ref="user-menu" :popup="true" :model="userMenuItems" />
      </template>
    </div>
    <form ref="logout-form" :action="logoutEndpoint" method="post">
      <input type="hidden" name="csrfmiddlewaretoken" :value="$csrfToken" />
    </form>
  </header>
</template>

<script setup lang="ts">
const { $csrfToken, $auth } = useNuxtApp();
const { logoutEndpoint } = useApiRepository();

const userMenuItems = computed(() => {
  if (!$auth.me.value || $auth.me.value === Unauthenticated) {
    return [];
  }
  const adminItems = $auth.me.value.is_staff ? [
    {
      label: 'Admin settings',
      url: '/admin',
    },
  ] : [];
  return [
    ...adminItems,
    {
      label: 'Sign out',
      command: () => {
        logoutForm.value?.submit();
      }
    },
  ];
});

const logoutForm = useTemplateRef('logout-form');

const userMenu = useTemplateRef('user-menu');
const toggleUserMenu = (event: MouseEvent) => {
  userMenu.value?.toggle(event);
};
</script>

