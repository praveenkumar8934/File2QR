import { fetchJson } from '@/lib/api';

export interface ShareLink {
  id: string;
  file_id: string;
  share_url?: string; // only available when raw_token is returned during creation
  is_active: boolean;
  created_at: string;
  revoked_at: string | null;
}

export const createShareLink = async (fileId: string, options?: { max_downloads?: number, password?: string, expires_at?: string }): Promise<ShareLink> => {
  return await fetchJson('/shares/', {
    method: 'POST',
    body: JSON.stringify({ file_id: fileId, ...options }),
  });
};

export const listShareLinks = async (): Promise<ShareLink[]> => {
  return await fetchJson('/shares/');
};

export const revokeShareLink = async (id: string): Promise<{status: string}> => {
  return await fetchJson(`/shares/${id}/revoke/`, {
    method: 'POST',
  });
};

export const updateShareLink = async (id: string, options: { max_downloads?: number | null, password?: string, expires_at?: string | null }): Promise<ShareLink> => {
  return await fetchJson(`/shares/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(options),
  });
};

export const regenerateShareToken = async (id: string): Promise<ShareLink> => {
  return await fetchJson(`/shares/${id}/regenerate-token/`, {
    method: 'POST',
  });
};

export interface PublicFile {
  filename: string;
  content_type: string;
  file_size: number;
  created_at: string;
  password_required: boolean;
  expires_at: string | null;
}

export const resolvePublicShare = async (token: string): Promise<PublicFile> => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/public/share/${token}/`, {
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error('Not found');
  }
  return res.json();
};

export const verifySharePassword = async (token: string, password: string): Promise<void> => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/public/share/${token}/verify-password/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
    credentials: 'include',
  });
  if (!res.ok) {
    if (res.status === 403) throw new Error('Incorrect password');
    throw new Error('Verification failed');
  }
};

export const downloadPublicShare = async (token: string): Promise<{download_url: string}> => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/public/share/${token}/download/`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!res.ok) {
    if (res.status === 403) {
      const data = await res.json().catch(() => ({}));
      if (data.error === 'Download limit reached') throw new Error('Download limit reached');
      if (data.error === 'Password required') throw new Error('Password required');
      if (data.error === 'Invalid authorization') throw new Error('Invalid authorization');
    }
    throw new Error('Download failed');
  }
  return res.json();
};
