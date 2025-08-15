import type {$Fetch, NitroFetchRequest} from 'nitropack'
import {FetchError} from "ofetch";

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
    try {
      return await fetch<User>('/api/me/', {
        method: 'GET',
        headers: {
          'accept': 'application/json',
        },
        gutenbergDisableUnauthenticatedHandling: true,
      });
    } catch (error) {
      if (!(error instanceof FetchError)) throw error;
      if (error.response?.status === 401 || error.response?.status === 403) {
        return Unauthenticated;
      }
      throw error;
    }
  },

  /**
   * This method should be called before login to rotate the CSRF token.
   */
  async refreshCsrfToken(): Promise<void> {
    await fetch('/api/login/', {
      method: 'GET',
    });
  },

  async login(username: string, password: string): Promise<void> {
    await fetch<User | null>('/api/login/', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
      },
      body: {
        username,
        password,
      },
    });
  },

  logoutEndpoint: '/oidc/logout/',
});

export function getErrorMessage(error: unknown): string | undefined {
  if (!(error instanceof FetchError)) return undefined;

  if (typeof error.data === 'object' && error.data !== null) {
    if ('message' in error.data && typeof error.data.message === 'string') {
      return error.data.message;
    }
  }

  if (error.response !== undefined) {
    return `Got HTTP error ${error.response.status}: ${error.response.statusText}`;
  }

  return 'Failed to connect to the server';
}
