'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchApi } from '@/lib/api';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const res = await fetchApi('/auth/register/', {
        method: 'POST',
        body: JSON.stringify({ email, password, first_name: firstName, last_name: lastName }),
      });

      if (res.ok) {
        // Redirect to login after successful registration
        router.push('/login');
      } else {
        const data = await res.json();
        if (data.email) setError(data.email[0]);
        else if (data.password) setError(data.password[0]);
        else setError('Registration failed. Please try again.');
      }
    } catch (e) {
      console.error(e);
      setError('An unexpected error occurred.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-[120px] mix-blend-screen pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/4 w-[30rem] h-[30rem] bg-indigo-600/10 rounded-full blur-[150px] mix-blend-screen pointer-events-none" />

      <div className="z-10 px-8 py-10 mx-4 glass-card w-full max-w-md rounded-2xl animate-fade-in shadow-2xl my-8">
        <div className="text-center mb-8">
          <Link href="/" className="inline-block text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400 mb-2 hover:opacity-80 transition-opacity">
            File2QR
          </Link>
          <h3 className="text-2xl font-bold text-white">Create an account</h3>
          <p className="text-gray-400 mt-2 text-sm">Join to start sharing files securely</p>
        </div>

        <form onSubmit={handleRegister} className="space-y-5">
          <div className="flex space-x-3">
            <div className="w-1/2">
              <label className="block text-sm font-medium text-gray-300 mb-1" htmlFor="firstName">First Name</label>
              <input type="text" id="firstName" placeholder="Jane"
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </div>
            <div className="w-1/2">
              <label className="block text-sm font-medium text-gray-300 mb-1" htmlFor="lastName">Last Name</label>
              <input type="text" id="lastName" placeholder="Doe"
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                value={lastName} onChange={(e) => setLastName(e.target.value)} />
            </div>
          </div>
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
            Register
          </button>
          
          <div className="text-center pt-4 border-t border-white/5">
            <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
              Already have an account? <span className="text-indigo-400 hover:underline">Log in</span>
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
