'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();
  const { refreshUser } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const res = await fetchApi('/auth/login/', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      if (res.ok) {
        await refreshUser();
        router.push('/dashboard');
      } else {
        const data = await res.json();
        setError(data.error || 'Failed to login');
      }
    } catch (e) {
      console.error(e);
      setError('An unexpected error occurred.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-[120px] mix-blend-screen pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[30rem] h-[30rem] bg-pink-600/10 rounded-full blur-[150px] mix-blend-screen pointer-events-none" />

      <div className="z-10 px-8 py-10 mx-4 glass-card w-full max-w-md rounded-2xl animate-fade-in shadow-2xl">
        <div className="text-center mb-8">
          <Link href="/" className="inline-block text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400 mb-2 hover:opacity-80 transition-opacity">
            File2QR
          </Link>
          <h3 className="text-2xl font-bold text-white">Welcome back</h3>
          <p className="text-gray-400 mt-2 text-sm">Sign in to manage your secure files</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1" htmlFor="email">Email address</label>
            <input type="email" placeholder="name@company.com" id="email"
              className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1" htmlFor="password">Password</label>
            <input type="password" placeholder="••••••••" id="password"
              className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm animate-pulse-slow">
              {error}
            </div>
          )}
          
          <button type="submit" className="w-full px-6 py-3 text-white font-medium bg-indigo-600 rounded-xl hover:bg-indigo-500 transition-all shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)] transform hover:-translate-y-0.5 mt-2">
            Sign In
          </button>
          
          <div className="text-center pt-4 border-t border-white/5">
            <Link href="/register" className="text-sm text-gray-400 hover:text-white transition-colors">
              Don&apos;t have an account? <span className="text-indigo-400 hover:underline">Register here</span>
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
