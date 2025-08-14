<template>
  <header class="fixed top-0 left-0 right-0 block h-(--header-height) bg-gray-800">
    <div class="px-4 h-full mx-auto max-w-5xl flex flex-row items-center justify-between">
      Gutenberg
      <Button v-if="me === Unauthenticated" label="Sign in" as="a" href="/login" variant="outlined" />
      <template v-else-if="me !== undefined">
        <Button variant="text" :label="me.username" aria-haspopup="menu" aria-controls="user_menu" @click="toggleUserMenu" />
        <Menu id="user_menu" ref="user-menu" :popup="true" :model="userMenuItems" />
      </template>
    </div>
  </header>
</template>

<script setup lang="ts">
const { me } = useAuth();

const userMenuItems = ref([
  {
    label: 'Sign out',
  },
  {
    label: 'Admin settings',
    url: '/admin',
  }
]);


const userMenu = useTemplateRef('user-menu');
const toggleUserMenu = (event: MouseEvent) => {
  userMenu.value?.toggle(event);
};
</script>

