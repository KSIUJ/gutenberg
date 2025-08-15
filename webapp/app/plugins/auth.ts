import {Unauthenticated} from "~/utils/api-repository";
import {FetchError} from "ofetch";

export default defineNuxtPlugin({
  dependsOn: ['api-plugin'],

  async setup() {
    const apiRepository = useApiRepository();

    const me = await useAsyncData('api-me', async (): Promise<User | typeof Unauthenticated> => {
      try {
        return await apiRepository.getMe() ?? Unauthenticated;
      } catch (error) {
        if (!(error instanceof FetchError)) throw error;
        if (error.response?.status === 401 || error.response?.status === 403) {
          return Unauthenticated;
        }
        throw error;
      }
    });

    const login = async (username: string, password: string) => {
      await apiRepository.refreshCsrfToken();
      await apiRepository.login(username, password);
      await me.refresh();
    };

    const auth = {
      me: me.data,
      login,
    };

    return {
      provide: {
        auth,
      },
    };
  },
});
