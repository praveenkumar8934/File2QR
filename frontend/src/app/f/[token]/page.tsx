'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { resolvePublicShare, PublicFile, verifySharePassword, downloadPublicShare } from '@/services/shareService';
import Link from 'next/link';

export default function PublicSharePage() {
  const params = useParams();
  const token = params.token as string;

  const [fileData, setFileData] = useState<PublicFile | null>(null);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(true);
  
  const [password, setPassword] = useState('');
  const [passwordVerified, setPasswordVerified] = useState(false);
  const [authError, setAuthError] = useState('');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let mounted = true;
    const loadData = async () => {
      try {
        const data = await resolvePublicShare(token);
        if (mounted) {
          setFileData(data);
          if (!data.password_required) {
            setPasswordVerified(true);
          }
        }
      } catch (err: unknown) {
        if (mounted) {
          if (err instanceof Error) {
            setError(err.message || 'This link is invalid, expired, or has been revoked.');
          } else {
            setError('This link is invalid, expired, or has been revoked.');
          }
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    if (token) {
      loadData();
    }
    return () => { mounted = false; };
  }, [token]);

  if (loading) {
    return <div className="min-h-screen bg-black flex items-center justify-center text-gray-400">Loading...</div>;
  }

  if (error || !fileData) {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-red-900/10 via-black to-black pointer-events-none" />
        
        <div className="glass-card p-10 rounded-3xl max-w-md w-full text-center shadow-2xl border border-white/10 relative z-10 animate-fade-in">
          <div className="w-20 h-20 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6 text-4xl shadow-[0_0_30px_rgba(239,68,68,0.15)]">
            🚫
          </div>
          <h1 className="text-3xl font-bold text-white mb-4">Link Unavailable</h1>
          <p className="text-gray-400 mb-8">{error}</p>
          <Link href="/" className="inline-block px-6 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-colors font-medium border border-white/5">
            Back to Home
          </Link>
        </div>
      </div>
    );
  }
  
  // using current time evaluated once to avoid impure function during render
  const now = new Date().getTime();
  const isExpired = fileData.expires_at && new Date(fileData.expires_at).getTime() < now;
  if (isExpired) {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-orange-900/10 via-black to-black pointer-events-none" />
        
        <div className="glass-card p-10 rounded-3xl max-w-md w-full text-center shadow-2xl border border-white/10 relative z-10 animate-fade-in">
          <div className="w-20 h-20 bg-orange-500/10 border border-orange-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6 text-4xl shadow-[0_0_30px_rgba(249,115,22,0.15)]">
            ⏳
          </div>
          <h1 className="text-3xl font-bold text-white mb-4">Link Expired</h1>
          <p className="text-gray-400 mb-8">This share link has expired and is no longer available.</p>
          <Link href="/" className="inline-block px-6 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-colors font-medium border border-white/5">
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    try {
      await verifySharePassword(token, password);
      setPasswordVerified(true);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setAuthError(err.message || 'Incorrect password');
      } else {
        setAuthError('Incorrect password');
      }
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    setAuthError('');
    try {
      const data = await downloadPublicShare(token);
      // Trigger download
      window.location.href = data.download_url;
    } catch (err: unknown) {
      if (err instanceof Error) {
        setAuthError(err.message || 'Download failed');
      } else {
        setAuthError('Download failed');
      }
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Decorative Background */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-pink-600/5 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="glass-card p-10 rounded-3xl max-w-md w-full shadow-2xl border border-white/10 text-center relative z-10 animate-slide-up">
        <div className="w-24 h-24 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-[0_0_40px_rgba(99,102,241,0.2)]">
          <svg className="w-10 h-10 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </div>
        
        <h1 className="text-2xl font-bold text-white mb-3 truncate px-2" title={fileData.filename}>
          {fileData.filename}
        </h1>
        
        <div className="flex justify-center items-center gap-3 text-sm text-gray-400 mb-10 bg-black/40 py-2 px-4 rounded-full w-fit mx-auto border border-white/5">
          <span className="font-medium text-gray-300">{formatSize(fileData.file_size)}</span>
          <span className="w-1 h-1 rounded-full bg-gray-600"></span>
          <span>{new Date(fileData.created_at).toLocaleDateString()}</span>
        </div>

        {!passwordVerified ? (
          <form onSubmit={handleVerify} className="space-y-5">
            <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-4 mb-6">
              <p className="text-orange-400/90 text-sm font-medium flex items-center justify-center gap-2">
                <span>🔒</span> This file is password protected
              </p>
            </div>
            
            <div>
              <input
                type="password"
                placeholder="Enter secure password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all text-center tracking-widest placeholder:tracking-normal"
                required
              />
            </div>
            {authError && <p className="text-red-400 text-sm animate-pulse">{authError}</p>}
            <button
              type="submit"
              className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] transform hover:-translate-y-0.5"
            >
              Unlock Access
            </button>
          </form>
        ) : (
          <div className="space-y-4 animate-fade-in">
            {authError && <p className="text-red-400 text-sm">{authError}</p>}
            <button 
              onClick={handleDownload}
              disabled={downloading}
              className={`w-full py-4 ${downloading ? 'bg-indigo-800/50 cursor-not-allowed' : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] transform hover:-translate-y-0.5'} text-white font-semibold rounded-xl transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)] flex items-center justify-center gap-3`}
            >
              {downloading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Preparing Download...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download File
                </>
              )}
            </button>
          </div>
        )}
      </div>
      
      <div className="mt-10 text-gray-500 text-sm flex items-center gap-2 z-10">
        <span className="opacity-50">Powered by</span>
        <Link href="/" className="font-semibold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400 opacity-80 hover:opacity-100 transition-opacity">
          File2QR
        </Link>
      </div>
    </div>
  );
}
