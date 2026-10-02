import { fetchJson } from '../lib/api';

export interface AnalyticsOverview {
  total_views: number;
  total_downloads: number;
  total_qr_scans: number;
  unique_visitors: number;
  active_shares: number;
  expired_shares: number;
  revoked_shares: number;
  date_range: {
    from: string;
    to: string;
  };
}

export interface AnalyticsTimeseries {
  date: string;
  views: number;
  downloads: number;
  qr_scans: number;
}

export interface FileAnalytics {
  file_id: string;
  filename: string;
  views: number;
  downloads: number;
  qr_scans: number;
  unique_visitors: number;
}

export interface ShareAnalytics {
  share_id: string;
  views: number;
  downloads: number;
  qr_scans: number;
  unique_visitors: number;
  password_success: number;
  password_failed: number;
  last_accessed: string | null;
  timeline: {
    event_type: string;
    date: string;
    device: string | null;
    browser: string | null;
    country: string | null;
    success: boolean;
  }[];
}

export interface QRAnalytics {
  qr_id: string;
  total_scans: number;
  unique_visitors: number;
  last_scan: string | null;
  device_breakdown: { device_type: string; count: number }[];
  browser_breakdown: { browser: string; count: number }[];
  os_breakdown: { os: string; count: number }[];
}

export async function getAnalyticsOverview(from?: string, to?: string): Promise<AnalyticsOverview> {
  let url = '/analytics/overview/';
  const params = new URLSearchParams();
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += `?${params.toString()}`;
  return fetchJson(url);
}

export async function getAnalyticsTimeseries(from?: string, to?: string): Promise<AnalyticsTimeseries[]> {
  let url = '/analytics/timeseries/';
  const params = new URLSearchParams();
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += `?${params.toString()}`;
  return fetchJson(url);
}

export async function getFileAnalytics(from?: string, to?: string): Promise<FileAnalytics[]> {
  let url = '/analytics/files/';
  const params = new URLSearchParams();
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += `?${params.toString()}`;
  return fetchJson(url);
}

export async function getShareAnalytics(shareId: string, from?: string, to?: string): Promise<ShareAnalytics> {
  let url = `/analytics/shares/${shareId}/`;
  const params = new URLSearchParams();
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += `?${params.toString()}`;
  return fetchJson(url);
}

export async function getQRAnalytics(qrId: string, from?: string, to?: string): Promise<QRAnalytics> {
  let url = `/analytics/qr/${qrId}/`;
  const params = new URLSearchParams();
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += `?${params.toString()}`;
  return fetchJson(url);
}
