<!-- See https://web.dev/articles/sign-in-form-best-practices?hl=en for login form best practices -->

<template>
  <div class="w-full max-w-md p-4 mx-auto">
    <Message v-if="sessionExpired" severity="warn" class="mb-4">
      <div class="w-full">Your session has expired</div>
      <div class="text-sm">Sign in again to continue</div>
    </Message>

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

const parseQuery = (route: RouteLocationNormalized) => ({
  next: getSingleQueryParam(route.query.next) ?? '/',
  expired: isQueryFlagEnabled(route.query.expired),
});

const sessionExpired = computed(() => parseQuery(route).expired);

const navigateToNext = (current: RouteLocationNormalized) => {
  const { next } = parseQuery(current);
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
  middleware: defineNuxtRouteMiddleware((to, from) => {
    // If the user is already authenticated, then skip the login page and go directly to the
    // route indicated in the `next` query param.

    // This redirect is disabled if the `expired` flag is set and the navigation is internal,
    // as the `$auth.me` value might not have been cleared yet if the session just expired.
    const isFirstRoute = to.fullPath == from.fullPath;
    if (!isFirstRoute && parseQuery(to).expired) return;

    const { $auth } = useNuxtApp();
    if ($auth.me.value === Unauthenticated) return;
    return navigateToNext(to);
  }),
});
</script>
