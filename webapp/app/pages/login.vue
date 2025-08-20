<!-- See https://web.dev/articles/sign-in-form-best-practices?hl=en for login form best practices -->

<template>
  <div class="w-full max-w-md p-4 mx-auto">
    <Panel header="Sign in to Gutenberg">
      <form method="post" class="space-y-4" @submit.prevent="onSubmit">
        <FloatLabel variant="in">
          <!--
            inputmode="email" is used to show the email keyboard on mobile devices.
            type="email" is not used here because it enforces e-mail validation,
            and the username does not necessarily have to be an email address.
          -->
          <InputText v-model="username" input-id="username" name="username" required type="text" autocomplete="username" inputmode="email" fluid autofocus />
          <label for="username">Username</label>
        </FloatLabel>
        <FloatLabel variant="in">
          <Password v-model="password" input-id="current-password" name="password" required autocomplete="current-password" fluid toggle-mask :feedback="false" />
          <label for="current-password">Password</label>
        </FloatLabel>

        <Message v-if="errorMessage !== null" severity="error">{{ errorMessage }}</Message>

        <div class="flex flex-row-reverse">
          <Button type="submit" label="Sign in" :disabled="loading" />
        </div>
      </form>
    </Panel>
  </div>
</template>

<script setup lang="ts">
import type {RouteLocationNormalized} from "#vue-router";

const { $auth } = useNuxtApp();
const route = useRoute();
const toast = useToast();

const username = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref<string | null>(null);

const extractNext = (route: RouteLocationNormalized) => {
  let result = route.query.next;
  if (result && typeof result !== 'string') result = result[0];
  return result || '/';
};

const navigateToNext = (current: RouteLocationNormalized) => {
  const next = extractNext(current);
  return navigateToMaybeExternal(next, current);
};

async function onSubmit() {
  if (loading.value) return;
  try {
    loading.value = true;
    errorMessage.value = null;
    await $auth.login(username.value, password.value);

    toast.add({
      summary: 'Login successful',
      severity: 'success',
      life: 3000,
    });

    await navigateToNext(route);
  } catch (error) {
    console.error('Failed to sign in', error);
    errorMessage.value = getErrorMessage(error) ?? 'Failed to sign in';
  } finally {
    loading.value = false;
  }
}

definePageMeta({
  hideSignInButton: true,
  middleware: defineNuxtRouteMiddleware((to) => {
    const { $auth } = useNuxtApp();
    if ($auth.me.value === Unauthenticated) return;
    return navigateToNext(to);
  }),
});
</script>
