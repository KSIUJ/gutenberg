import type {$Fetch, NitroFetchRequest} from 'nitropack'

export type User = {
  first_name: string;
  last_name: string;
  username: string;
  api_key: string;
  is_staff: boolean;
};

export const Unauthenticated = Symbol('Unauthenticated');

export const apiRepository = <T>(fetch: $Fetch<T, NitroFetchRequest>) => ({
  async getMe(): Promise<User | typeof Unauthenticated> {
    return await fetch<User | null>('/api/me', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'accept': 'application/json',
      },
    }) ?? Unauthenticated;
  }
})
