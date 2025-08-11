import type {$Fetch, NitroFetchRequest} from 'nitropack'

type User = {
  first_name: string;
  last_name: string;
  username: string;
  api_key: string;
  is_staff: boolean;
};

export const apiRepository = <T>(fetch: $Fetch<T, NitroFetchRequest>) => ({
  async getMe(): Promise<User> {
    return await fetch<User>('/api/me', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'accept': 'application/json',
      },
    });
  }
})
