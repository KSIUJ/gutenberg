import type { $Fetch, NitroFetchRequest } from 'nitropack';
import { FetchError } from 'ofetch';

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
  two_sides: ApiDuplexMode;
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

export type ListResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export const Unauthenticated = Symbol('Unauthenticated');

export const createApiRepository = <T>(fetch: $Fetch<T, NitroFetchRequest>) => ({
  async getMe(): Promise<User | typeof Unauthenticated> {
    try {
      return await fetch<User>('/api/me/', {
        method: 'GET',
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
      gutenbergExpectJson: false,
    });
  },

  async login(username: string, password: string): Promise<void> {
    await fetch('/api/login/', {
      method: 'POST',
      body: {
        username,
        password,
      },
      gutenbergExpectJson: false,
    });
  },

  logoutEndpoint: '/oidc/logout/',

  async getPrinters(): Promise<Printer[]> {
    return await fetch<Printer[]>('/api/printers/', {
      method: 'GET',
    });
  },

  async createPrintJob(body: CreatePrintJobRequest): Promise<PrintJob> {
    return await fetch<PrintJob>('/api/jobs/create_job/', {
      method: 'POST',
      body,
    });
  },

  async uploadArtefact(jobId: number, file: File, last: boolean): Promise<PrintJob> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('last', last ? '1' : '0');
    return await fetch<PrintJob>(`/api/jobs/${jobId}/upload_artefact/`, {
      method: 'POST',
      body: formData,
    });
  },

  async runJob(jobId: number): Promise<PrintJob> {
    return await fetch<PrintJob>(`/api/jobs/${jobId}/run_job/`, {
      method: 'POST',
    });
  },

  async cancelPrintJob(jobId: number): Promise<PrintJob> {
    return await fetch<PrintJob>(`/api/jobs/${jobId}/cancel/`, {
      method: 'POST',
    });
  },

  async listJobs(pageSize: number = 1000): Promise<ListResponse<PrintJob>> {
    return await fetch<ListResponse<PrintJob>>(`/api/jobs/`, {
      query: {
        page_size: pageSize,
      },
      method: 'GET',
    });
  },

  async getJob(jobId: number): Promise<PrintJob> {
    return await fetch<PrintJob>(`/api/jobs/${jobId}/`, {
      method: 'GET',
    });
  },

  async resetIppToken(): Promise<void> {
    await fetch('/api/resettoken/', {
      method: 'POST',
      gutenbergExpectJson: false,
    });
  },

  createIppUri(ippToken: string | null, printerId: number) {
    const useHttps = window.location.protocol === 'https:';
    const [proto, defaultPort] = useHttps ? ['ipps://', '443'] : ['ipp://', '80'];
    const port = window.location.port || defaultPort;
    return `${proto}${window.location.hostname}:${port}/ipp/${ippToken ?? 'basic'}/${printerId}/print`;
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
