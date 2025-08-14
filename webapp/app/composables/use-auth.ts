import {FetchError} from 'ofetch';
import {Unauthenticated} from "~/utils/api-repository";

export const useAuth = () => {
  const apiRepository = useApiRepository();
  const me = useAsyncData(async (): Promise<User | typeof Unauthenticated> => {
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

  return {
    me: me.data,
  }
};
