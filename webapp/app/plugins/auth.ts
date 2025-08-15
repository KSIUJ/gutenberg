import {Unauthenticated} from "~/utils/api-repository";

export default defineNuxtPlugin({
  name: 'auth-plugin',
  dependsOn: ['api-plugin'],

  async setup() {
    const apiRepository = useApiRepository();

    const me = await useAsyncData('api-me', async (): Promise<User | typeof Unauthenticated> => {
      return await apiRepository.getMe();
    });

    const login = async (username: string, password: string) => {
      await apiRepository.refreshCsrfToken();
      await apiRepository.login(username, password);
      await me.refresh();
    };

    /**
     * Set the `me` value to `Unauthenticated`.
     * This function is intended to be used by the error handler is the API plugin.
     */
    const clearMe = () => {
      me.data.value = Unauthenticated;
    };

    const auth = {
      me: me.data,
      clearMe,
      login,
    };

    return {
      provide: {
        auth,
      },
    };
  },
});
