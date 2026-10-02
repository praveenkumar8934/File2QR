'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { uploadFile, loadFilesList, deleteFile } from '@/services/fileService';
import { createShareLink } from '@/services/shareService';
import { generateQRCode } from '@/services/qrService';
import Link from 'next/link';

type FileRecord = {
  id: string;
  original_filename: string;
  file_size: number;
  content_type: string;
  status: string;
  created_at: string;
};

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [shareConfigModal, setShareConfigModal] = useState<FileRecord | null>(null);
  const [sharePassword, setSharePassword] = useState('');
  const [shareMaxDownloads, setShareMaxDownloads] = useState('');
  const [shareExpiresInDays, setShareExpiresInDays] = useState('');

  const loadFiles = async () => {
    try {
      const data = await loadFilesList();
      setFiles(data);
    } catch (e: unknown) {
      if (e instanceof Error && e.name === 'AuthError') return;
      console.error('Failed to load files', e);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (user) loadFiles();
  }, [user]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setError('');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setProgress(10);
    setError('');

    try {
      await uploadFile(selectedFile, setProgress);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await loadFiles();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'An error occurred during upload.');
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };

  const handleDelete = async (fileId: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return;
    try {
      await deleteFile(fileId);
      await loadFiles();
    } catch (e) {
      console.error(e);
      alert('Failed to delete file');
    }
  };

  return (
    <div className="min-h-screen bg-black relative">
      {/* Background Glow */}
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-indigo-900/20 to-transparent pointer-events-none" />
      
      <nav className="glass-card sticky top-0 z-40 px-6 py-4 flex justify-between items-center border-b-0 border-white/5">
        <Link href="/" className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400">
          File2QR
        </Link>
        <div className="flex gap-6 items-center">
          <Link href="/dashboard" className="text-white font-medium">Files</Link>
          <Link href="/dashboard/shares" className="text-gray-400 hover:text-white transition-colors">Shares</Link>
          <Link href="/dashboard/qr-codes" className="text-gray-400 hover:text-white transition-colors">QR Codes</Link>
          <Link href="/dashboard/analytics" className="text-gray-400 hover:text-white transition-colors">Analytics</Link>
          <div className="h-6 w-px bg-white/10 mx-2"></div>
          <button onClick={logout} className="text-gray-400 hover:text-pink-400 transition-colors text-sm font-medium">Logout</button>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto mt-10 p-6 z-10 relative animate-fade-in">
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">My Files</h1>
            <p className="text-gray-400">Upload and manage your secure files</p>
          </div>
        </div>

        {/* Upload Dropzone */}
        <div className="glass-card rounded-2xl p-8 mb-10 text-center border-dashed border-2 border-indigo-500/30 hover:border-indigo-500/60 transition-colors relative"
             onDragOver={e => e.preventDefault()} onDrop={handleDrop}>
          <input type="file" ref={fileInputRef} onChange={handleFileChange} disabled={uploading} className="hidden" id="file-upload" />
          
          {!selectedFile ? (
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center justify-center py-8">
              <div className="w-16 h-16 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 text-3xl mb-4">
                📁
              </div>
              <h3 className="text-xl font-medium text-white mb-2">Click or drag a file to upload</h3>
              <p className="text-gray-500 text-sm max-w-sm">Securely upload any file. It will be encrypted and stored safely on Cloudflare R2.</p>
            </label>
          ) : (
            <div className="py-6">
              <div className="flex items-center justify-center gap-4 mb-6">
                <div className="text-4xl">📄</div>
                <div className="text-left">
                  <p className="text-white font-medium text-lg">{selectedFile.name}</p>
                  <p className="text-gray-400 text-sm">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                {!uploading && (
                  <button onClick={() => { setSelectedFile(null); if(fileInputRef.current) fileInputRef.current.value = ''; }} className="ml-4 text-gray-500 hover:text-white p-2">✕</button>
                )}
              </div>

              {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

              {uploading ? (
                <div className="max-w-md mx-auto">
                  <div className="flex justify-between text-xs text-indigo-300 mb-1">
                    <span>Uploading...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-black/50 rounded-full h-2 border border-white/10 overflow-hidden">
                    <div className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
                  </div>
                </div>
              ) : (
                <button onClick={handleUpload} className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium transition-all shadow-[0_0_20px_rgba(79,70,229,0.3)]">
                  Confirm Upload
                </button>
              )}
            </div>
          )}
        </div>

        {/* File List */}
        <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
          <div className="p-6 border-b border-white/5 bg-white/5">
            <h2 className="text-lg font-semibold text-white">Uploaded Files</h2>
          </div>
          
          {files.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              <div className="text-4xl mb-4 opacity-50">🗄️</div>
              <p>No files uploaded yet.</p>
            </div>
          ) : (
            <ul className="divide-y divide-white/5">
              {files.map(file => (
                <li key={file.id} className="p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center hover:bg-white/[0.02] transition-colors gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded bg-indigo-500/20 flex items-center justify-center text-indigo-400 text-xl">
                      📄
                    </div>
                    <div>
                      <p className="font-medium text-white truncate max-w-[200px] sm:max-w-xs">{file.original_filename}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {(file.file_size / 1024 / 1024).toFixed(2)} MB • {new Date(file.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2 w-full sm:w-auto">
                    <button
                      onClick={() => {
                        setShareConfigModal(file);
                        setSharePassword('');
                        setShareMaxDownloads('');
                        setShareExpiresInDays('');
                      }}
                      className="flex-1 sm:flex-none px-4 py-2 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-lg text-sm font-medium hover:bg-indigo-500/30 transition-colors"
                    >
                      Share / QR
                    </button>
                    <button 
                      onClick={() => handleDelete(file.id)}
                      className="px-3 py-2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-sm font-medium hover:bg-red-500/20 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>

      {/* Share Modal */}
      {shareConfigModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="glass-card bg-[#0a0a0a]/90 p-8 rounded-2xl max-w-md w-full border border-white/10 shadow-2xl animate-slide-up">
            <h2 className="text-2xl font-bold text-white mb-2">Create Secure Share</h2>
            <p className="text-sm text-gray-400 mb-6 truncate">For: {shareConfigModal.original_filename}</p>
            
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Password (Optional)</label>
                <input type="password" placeholder="Leave blank for public link" value={sharePassword} onChange={e => setSharePassword(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 text-white rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="flex gap-4">
                <div className="w-1/2">
                  <label className="block text-sm font-medium text-gray-300 mb-1">Max Downloads</label>
                  <input type="number" min="1" placeholder="Unlimited" value={shareMaxDownloads} onChange={e => setShareMaxDownloads(e.target.value)}
                    className="w-full bg-black/50 border border-white/10 text-white rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div className="w-1/2">
                  <label className="block text-sm font-medium text-gray-300 mb-1">Expires In (Days)</label>
                  <input type="number" min="1" placeholder="Never" value={shareExpiresInDays} onChange={e => setShareExpiresInDays(e.target.value)}
                    className="w-full bg-black/50 border border-white/10 text-white rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
              </div>
              
              <div className="flex justify-end gap-3 mt-8">
                <button type="button" onClick={() => setShareConfigModal(null)} className="px-5 py-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                  Cancel
                </button>
                <button 
                  onClick={async () => {
                    try {
                      let expires_at = undefined;
                      if (shareExpiresInDays) {
                        const date = new Date();
                        date.setDate(date.getDate() + parseInt(shareExpiresInDays));
                        expires_at = date.toISOString();
                      }
                      
                      const share = await createShareLink(shareConfigModal.id, {
                        password: sharePassword || undefined,
                        max_downloads: shareMaxDownloads ? parseInt(shareMaxDownloads) : undefined,
                        expires_at
                      });
                      
                      if (share.share_url) {
                        await navigator.clipboard.writeText(share.share_url);
                        alert('Share link copied to clipboard!');
                        
                        const rawToken = share.share_url.split('/').pop() || '';
                        await generateQRCode(share.id, rawToken);
                      }
                      setShareConfigModal(null);
                    } catch (e) {
                      console.error(e);
                      alert('Failed to create secure share link.');
                    }
                  }}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(79,70,229,0.4)]"
                >
                  Create & Copy Link
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
