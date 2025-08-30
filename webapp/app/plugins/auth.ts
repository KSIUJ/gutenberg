import { Unauthenticated } from '~/utils/api-repository';

export default defineNuxtPlugin({
  name: 'auth-plugin',
  dependsOn: ['api-plugin'],

  async setup() {
    const apiRepository = useApiRepository();

    // The auth plugin returns a Promise (is async) to make sure the authentication info is loaded
    // when the app is rendered.
    // Failing to load the auth info is a fatal error because the routing logic needs to know if
    // the user is signed in to handle redirects to the sign-in page.
    let me: Ref<User | typeof Unauthenticated>;
    try {
      me = ref(await apiRepository.getMe());
    } catch (error) {
      throw createError({
        message: 'Failed to load information about the current user',
        cause: error,
        fatal: true,
      });
    }

    const login = async (username: string, password: string) => {
      await apiRepository.refreshCsrfToken();
      await apiRepository.login(username, password);
      me.value = await apiRepository.getMe();
    };

    /**
     * Set the `me` value to `Unauthenticated`.
     * This function is intended to be used by the error handler is the API plugin.
     */
    const clearMe = () => {
      me.value = Unauthenticated;
    };

    const resetIppToken = async () => {
      await apiRepository.resetIppToken();
      me.value = await apiRepository.getMe();
    };

    const auth = {
      me: readonly(me),
      clearMe,
      login,
      resetIppToken,
    };

    return {
      provide: {
        auth,
      },
    };
  },
});
