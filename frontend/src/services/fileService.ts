import { fetchJson } from '@/lib/api';

export const uploadFile = async (file: File, setProgress: (p: number) => void) => {
  setProgress(10);
  // 1. Get presigned URL
  const urlRes = await fetchJson('/files/upload-url/', {
    method: 'POST',
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type,
      file_size: file.size
    })
  });
  
  setProgress(40);
  const { upload_url, file_id } = urlRes;

  // 2. Direct PUT to R2/S3
  const putRes = await fetch(upload_url, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type
    }
  });

  if (!putRes.ok) {
    throw new Error('Failed to upload file to storage');
  }
  setProgress(80);

  // 3. Confirm upload
  await fetchJson(`/files/${file_id}/confirm-upload/`, {
    method: 'POST'
  });

  setProgress(100);
};

export const loadFilesList = async () => {
  return await fetchJson('/files/');
};

export const deleteFile = async (fileId: string) => {
  await fetchJson(`/files/${fileId}/`, {
    method: 'DELETE'
  });
};
