const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

function getCsrfToken() {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
  return match ? match[2] : null;
}

let refreshPromise: Promise<boolean> | null = null;

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_URL}${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const method = (options.method || 'GET').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    let token = getCsrfToken();
    if (!token) {
      await fetch(`${API_URL}/auth/csrf/`, { credentials: 'include' });
      token = getCsrfToken();
    }
    if (token) {
      headers.set('X-CSRFToken', token);
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Ensures HttpOnly cookies are sent
  });

  if (response.status === 401) {
    if (endpoint.includes('/auth/refresh/')) {
        if (typeof window !== 'undefined') {
            window.dispatchEvent(new Event('auth_error'));
        }
        return response;
    }

    if (!endpoint.includes('/auth/logout/')) {
        if (!refreshPromise) {
            refreshPromise = (async () => {
                const refreshHeaders = new Headers();
                const csrfToken = getCsrfToken();
                if (csrfToken) {
                    refreshHeaders.set('X-CSRFToken', csrfToken);
                }

                const refreshResponse = await fetch(`${API_URL}/auth/refresh/`, {
                    method: 'POST',
                    headers: refreshHeaders,
                    credentials: 'include'
                });
                
                const ok = refreshResponse.ok;
                if (!ok) {
                    if (typeof window !== 'undefined') {
                        window.dispatchEvent(new Event('auth_error'));
                    }
                }
                return ok;
            })().finally(() => {
                refreshPromise = null;
            });
        }
        
        const ok = await refreshPromise;
        if (ok) {
            // Re-fetch CSRF token if necessary after refresh
            const newCsrfToken = getCsrfToken();
            if (newCsrfToken && headers.has('X-CSRFToken')) {
                headers.set('X-CSRFToken', newCsrfToken);
            }
            return fetch(url, {
                ...options,
                headers,
                credentials: 'include'
            });
        }
    }
  }

  return response;
}

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthError';
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function fetchJson<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetchApi(endpoint, options);
  if (res.status === 401) {
    throw new AuthError(`API Error: ${res.status}`);
  }
  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`);
  }
  if (res.status !== 204) {
    return res.json();
  }
  return {} as T;
}
