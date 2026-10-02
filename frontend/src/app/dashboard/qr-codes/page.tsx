'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { QRCode, listQRCodes, deactivateQRCode, downloadQRCode } from '@/services/qrService';
import Link from 'next/link';

export default function QRCodesPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  
  const [qrs, setQrs] = useState<QRCode[]>([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  const loadQRCodes = async () => {
    try {
      setFetching(true);
      const data = await listQRCodes();
      setQrs(data);
    } catch (e: unknown) {
      if (e instanceof Error && e.name === 'AuthError') return;
      if (e instanceof Error) {
        setError(e.message || 'Failed to load QR codes.');
      } else {
        setError('Failed to load QR codes.');
      }
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    if (user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadQRCodes();
    }
  }, [user]);

  const handleDeactivate = async (id: string) => {
    try {
      await deactivateQRCode(id);
      await loadQRCodes();
    } catch (e: unknown) {
      console.error(e);
      alert('Failed to deactivate QR code');
    }
  };

  const handleDownload = async (id: string) => {
    try {
      const res = await downloadQRCode(id);
      window.open(res.download_url, '_blank');
    } catch (e: unknown) {
      console.error(e);
      alert('Failed to get download URL for QR code');
    }
  };

  if (loading || fetching) return <div className="min-h-screen bg-black flex items-center justify-center text-gray-400">Loading...</div>;

  return (
    <div className="min-h-screen bg-black relative">
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-indigo-900/20 to-transparent pointer-events-none" />
      
      <nav className="glass-card sticky top-0 z-40 px-6 py-4 flex justify-between items-center border-b-0 border-white/5">
        <Link href="/" className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400">
          File2QR
        </Link>
        <div className="flex gap-6 items-center">
          <Link href="/dashboard" className="text-gray-400 hover:text-white transition-colors">Files</Link>
          <Link href="/dashboard/shares" className="text-gray-400 hover:text-white transition-colors">Shares</Link>
          <Link href="/dashboard/qr-codes" className="text-white font-medium">QR Codes</Link>
          <div className="h-6 w-px bg-white/10 mx-2"></div>
          <button onClick={logout} className="text-gray-400 hover:text-pink-400 transition-colors text-sm font-medium">Logout</button>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto mt-10 p-6 z-10 relative animate-fade-in">
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">My QR Codes</h1>
            <p className="text-gray-400">Manage and download your generated QR codes</p>
          </div>
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl mb-6">{error}</div>}

        <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
          <div className="p-6 border-b border-white/5 bg-white/5">
            <h2 className="text-lg font-semibold text-white">Generated Codes</h2>
          </div>
          
          {qrs.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              <div className="text-4xl mb-4 opacity-50">📱</div>
              <p>You haven&apos;t generated any QR codes yet.</p>
            </div>
          ) : (
            <ul className="divide-y divide-white/5">
              {qrs.map(qr => (
                <li key={qr.id} className="p-6 flex flex-col md:flex-row justify-between items-start md:items-center hover:bg-white/[0.02] transition-colors gap-4">
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded flex items-center justify-center text-xl mt-1 ${qr.is_active ? 'bg-indigo-500/20 text-indigo-400' : 'bg-red-500/10 text-red-400'}`}>
                      {qr.is_active ? '📱' : '🚫'}
                    </div>
                    <div>
                      <p className="font-medium text-white truncate max-w-[200px] sm:max-w-xs mb-1">{qr.filename}</p>
                      <p className="text-xs text-gray-500 mb-2">Created: {new Date(qr.created_at).toLocaleString()}</p>
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${qr.is_active ? 'bg-green-500/20 text-green-400 border border-green-500/20' : 'bg-red-500/20 text-red-400 border border-red-500/20'}`}>
                        {qr.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 w-full md:w-auto mt-4 md:mt-0 flex-wrap">
                    <button
                      onClick={() => handleDownload(qr.id)}
                      className="px-4 py-2 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-lg text-sm font-medium hover:bg-indigo-500/30 transition-colors"
                    >
                      Download
                    </button>
                    {qr.is_active && (
                      <button
                        onClick={() => handleDeactivate(qr.id)}
                        className="px-4 py-2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-sm font-medium hover:bg-red-500/20 transition-colors"
                      >
                        Deactivate
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}
