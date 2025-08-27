import type {$Fetch, NitroFetchRequest} from 'nitropack'
import {FetchError} from "ofetch";

export type User = {
  first_name: string;
  last_name: string;
  username: string;
  api_key: string;
  is_staff: boolean;
};

export type Printer = {
  id: number;
  name: string;
  color_allowed: boolean;
  duplex_supported: boolean;
  supported_extensions: string;
};

/**
 * One-sided | Two-sided long edge | Two-sided short edge
 */
export type ApiDuplexMode = 'OS' | 'TL' | 'TS';

export type CreatePrintJobRequest = {
  printer: number;
  copies: number;
  pages_to_print?: string;
  two_sides: ApiDuplexMode,
  color?: boolean;
  fit_to_page?: boolean;
};

export type JobStatus = 'UNKNOWN' | 'INCOMING' | 'PENDING' | 'PROCESSING' | 'PRINTING' | 'SCANNING' | 'WAITING_PAGE' | 'COMPLETED' | 'CANCELED' | 'CANCELING' | 'ERROR';

export type PrintJob = {
  id: number;
  pages: number | null;
  printer: string | null;
  status: JobStatus;
  status_reason: string | null;
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

  async getPrinters(): Promise<Printer[]> {
    return await fetch<Printer[]>('/api/printers/', {
      method: 'GET',
      headers: {
        'accept': 'application/json',
      },
    });
  },

  async createPrintJob(body: CreatePrintJobRequest): Promise<PrintJob> {
    return await fetch<PrintJob>('/api/jobs/create_job/', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
      },
      body,
    });
  },

  async uploadArtefact(jobId: number, file: File, last: boolean): Promise<PrintJob> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('last', last ? '1' : '0');
    return await fetch<PrintJob>(`/api/jobs/${jobId}/upload_artefact/`, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
      },
      body: formData,
    });
  },

  async runJob(jobId: number): Promise<PrintJob> {
    return await fetch<PrintJob>(`/api/jobs/${jobId}/run_job/`, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
      },
    });
  },

  async cancelPrintJob(jobId: number): Promise<PrintJob> {
    return await fetch<PrintJob>(`/api/jobs/${jobId}/cancel/`, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
      },
    });
  },
});

export function getErrorMessage(error: unknown): string | undefined {
  if (isNuxtError(error)) {
    return getErrorMessage(error.cause) ?? error.message;
  }
  if (!(error instanceof FetchError)) return undefined;
  const responseIsJson = error?.response?.headers?.get('content-type')?.startsWith('application/json') ?? false;

  if (responseIsJson && typeof error.data === 'string') return error.data;
  if (typeof error.data === 'object' && error.data !== null) {
    if ('message' in error.data && typeof error.data.message === 'string') {
      return error.data.message;
    }
    if ('detail' in error.data && typeof error.data.detail === 'string') {
      return error.data.detail;
    }
  }

  if (error.response !== undefined) {
    return `Got HTTP error ${error.response.status}: ${error.response.statusText}`;
  }

  return 'Failed to connect to the server';
}
