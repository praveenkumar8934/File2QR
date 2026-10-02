'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ShareLink, listShareLinks, revokeShareLink, updateShareLink, regenerateShareToken } from '@/services/shareService';
import Link from 'next/link';

export default function SharesPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  
  const [shares, setShares] = useState<ShareLink[]>([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');

  const [editingShare, setEditingShare] = useState<ShareLink | null>(null);
  const [editPassword, setEditPassword] = useState('');
  const [editMaxDownloads, setEditMaxDownloads] = useState('');

  const loadShares = async () => {
    try {
      setFetching(true);
      const data = await listShareLinks();
      setShares(data);
    } catch (e: unknown) {
      if (e instanceof Error && e.name === 'AuthError') return;
      console.error(e);
      setError('Failed to load share links.');
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    if (user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadShares();
    }
  }, [user]);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  const handleRevoke = async (id: string) => {
    if (!confirm('Are you sure you want to revoke this share link?')) return;
    try {
      await revokeShareLink(id);
      await loadShares();
    } catch (e) {
      console.error(e);
      alert('Failed to revoke share link');
    }
  };

  const handleRegenerate = async (id: string) => {
    if (!confirm('This will invalidate the current link and QR code. Continue?')) return;
    try {
      const share = await regenerateShareToken(id);
      if (share.share_url) {
        alert('Token regenerated. A new QR code has also been generated.');
      }
      await loadShares();
    } catch (e) {
      console.error(e);
      alert('Failed to regenerate token');
    }
  };

  const submitEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingShare) return;
    try {
      await updateShareLink(editingShare.id, {
        password: editPassword || undefined,
        max_downloads: editMaxDownloads ? parseInt(editMaxDownloads) : null
      });
      setEditingShare(null);
      await loadShares();
      alert('Share link updated successfully.');
    } catch (err) {
      console.error(err);
      alert('Failed to update share link.');
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
          <Link href="/dashboard/shares" className="text-white font-medium">Shares</Link>
          <Link href="/dashboard/qr-codes" className="text-gray-400 hover:text-white transition-colors">QR Codes</Link>
          <div className="h-6 w-px bg-white/10 mx-2"></div>
          <button onClick={logout} className="text-gray-400 hover:text-pink-400 transition-colors text-sm font-medium">Logout</button>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto mt-10 p-6 z-10 relative animate-fade-in">
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Manage Shares</h1>
            <p className="text-gray-400">View and edit your secure share links</p>
          </div>
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl mb-6">{error}</div>}

        <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
          <div className="p-6 border-b border-white/5 bg-white/5">
            <h2 className="text-lg font-semibold text-white">Active & Revoked Links</h2>
          </div>
          
          {shares.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              <div className="text-4xl mb-4 opacity-50">🔗</div>
              <p>You haven&apos;t created any share links yet.</p>
            </div>
          ) : (
            <ul className="divide-y divide-white/5">
              {shares.map(share => (
                <li key={share.id} className="p-6 flex flex-col md:flex-row justify-between items-start md:items-center hover:bg-white/[0.02] transition-colors gap-4">
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded flex items-center justify-center text-xl mt-1 ${share.is_active ? 'bg-indigo-500/20 text-indigo-400' : 'bg-red-500/10 text-red-400'}`}>
                      {share.is_active ? '🔗' : '🚫'}
                    </div>
                    <div>
                      <p className="font-medium text-white truncate max-w-[200px] sm:max-w-xs mb-1">
                        Share ID: {share.id.split('-')[0]}...
                      </p>
                      <p className="text-xs text-gray-500 mb-2">Created: {new Date(share.created_at).toLocaleString()}</p>
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${share.is_active ? 'bg-green-500/20 text-green-400 border border-green-500/20' : 'bg-red-500/20 text-red-400 border border-red-500/20'}`}>
                        {share.is_active ? 'ACTIVE' : 'REVOKED'}
                      </span>
                    </div>
                  </div>
                  
                  {share.is_active && (
                    <div className="flex gap-2 w-full md:w-auto mt-4 md:mt-0 flex-wrap">
                      <button
                        onClick={() => {
                          setEditingShare(share);
                          setEditPassword('');
                          setEditMaxDownloads('');
                        }}
                        className="px-4 py-2 bg-white/5 text-white border border-white/10 rounded-lg text-sm font-medium hover:bg-white/10 transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleRegenerate(share.id)}
                        className="px-4 py-2 bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 rounded-lg text-sm font-medium hover:bg-yellow-500/20 transition-colors"
                      >
                        Regen Token
                      </button>
                      <button
                        onClick={() => handleRevoke(share.id)}
                        className="px-4 py-2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-sm font-medium hover:bg-red-500/20 transition-colors"
                      >
                        Revoke
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>

      {editingShare && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="glass-card bg-[#0a0a0a]/90 p-8 rounded-2xl max-w-md w-full border border-white/10 shadow-2xl animate-slide-up">
            <h2 className="text-2xl font-bold text-white mb-2">Edit Share Link</h2>
            <p className="text-sm text-gray-400 mb-6 truncate">ID: {editingShare.id}</p>
            
            <form onSubmit={submitEdit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">New Password (leave blank to keep current)</label>
                <input type="password" value={editPassword} onChange={e => setEditPassword(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 text-white rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Max Downloads (leave blank for unlimited)</label>
                <input type="number" min="1" placeholder="e.g. 5" value={editMaxDownloads} onChange={e => setEditMaxDownloads(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 text-white rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              
              <div className="flex justify-end gap-3 mt-8">
                <button type="button" onClick={() => setEditingShare(null)} className="px-5 py-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(79,70,229,0.4)]">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
