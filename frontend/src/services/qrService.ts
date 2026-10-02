import { fetchJson } from '@/lib/api';

export interface QRCode {
  id: string;
  share_link_id: string;
  file_id: string;
  filename: string;
  is_active: boolean;
  created_at: string;
}

export const generateQRCode = async (shareLinkId: string, rawToken: string): Promise<QRCode> => {
  return await fetchJson('/qr-codes/', {
    method: 'POST',
    body: JSON.stringify({ 
      share_link_id: shareLinkId,
      raw_token: rawToken
    }),
  });
};

export const listQRCodes = async (): Promise<QRCode[]> => {
  return await fetchJson('/qr-codes/');
};

export const downloadQRCode = async (id: string): Promise<{download_url: string}> => {
  return await fetchJson(`/qr-codes/${id}/download/`, {
    method: 'GET',
  });
};

export const deactivateQRCode = async (id: string): Promise<{status: string}> => {
  return await fetchJson(`/qr-codes/${id}/`, {
    method: 'DELETE',
  });
};
