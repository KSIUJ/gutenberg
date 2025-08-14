<!-- See https://web.dev/articles/sign-in-form-best-practices?hl=en for login form best practices -->

<template>
  <div class="w-full max-w-md p-4 mx-auto">
    <Panel header="Login to Gutenberg">
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

        <div class="flex flex-row-reverse">
          <Button type="submit" label="Login" :disabled="loading" />
        </div>
      </form>
    </Panel>
  </div>
</template>

<script setup lang="ts">
import { Unauthenticated } from "~/utils/api-repository";

const { data: me } = await useAuthMe();
const auth = await useAuth();
const route = useRoute();
const toast = useToast();

const username = ref('');
const password = ref('');
const loading = ref(false);

const next = computed(() => {
  let result = route.query.next;
  if (result && typeof result !== 'string') result = result[0];
  return result || '/';
});

async function onSubmit() {
  if (loading.value) return;
  try {
    loading.value = true;
    await new Promise((resolve) => setTimeout(resolve, 1000));
    await auth.login(username.value, password.value);
    try {
      await navigateTo(next.value);
    } catch (error) {
      console.warn(`Internal navigation to ${next.value} failed`, error);
      await navigateTo(next.value, {
        external: true,
      });
    }

    toast.add({
      summary: 'Login successful',
      severity: 'success',
      life: 3000,
    });
  } catch (error) {
    alert(error); // TODO
    console.error('Failed to login', error);
  } finally {
    loading.value = false;
  }
}

watchEffect(async () => {
  if (me.value === undefined || me.value === Unauthenticated) return;
  try {
    await navigateTo(next.value);
  } catch (error) {
    console.warn(`Failed to navigate to ${next.value} after successful login`, error);
    window.location.href = next.value;
  }
});
</script>
