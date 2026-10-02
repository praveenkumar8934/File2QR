import Link from 'next/link';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-[120px] mix-blend-screen pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[30rem] h-[30rem] bg-pink-600/10 rounded-full blur-[150px] mix-blend-screen pointer-events-none" />

      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full">
        <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400">
          File2QR
        </div>
        <nav className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
            Sign In
          </Link>
          <Link href="/register" className="text-sm font-medium px-5 py-2 rounded-full bg-white/10 hover:bg-white/20 border border-white/10 transition-all shadow-lg hover:shadow-indigo-500/20">
            Get Started
          </Link>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 z-10 animate-slide-up">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            Secure Cloudflare R2 Uploads
          </div>
          
          <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white mb-8 leading-tight">
            Share Files Securely, <br className="hidden sm:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 glow-text">
              Anywhere in Seconds.
            </span>
          </h1>
          
          <p className="mt-4 text-xl sm:text-2xl text-gray-400 max-w-2xl mx-auto mb-10 font-light leading-relaxed">
            Upload files, generate password-protected links with download limits, and instantly create custom QR codes for seamless offline-to-online sharing.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link 
              href="/register" 
              className="w-full sm:w-auto px-8 py-4 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold text-lg hover:from-indigo-500 hover:to-purple-500 transition-all shadow-[0_0_40px_rgba(79,70,229,0.4)] hover:shadow-[0_0_60px_rgba(79,70,229,0.6)] transform hover:-translate-y-1"
            >
              Start Sharing Free
            </Link>
            <Link 
              href="/dashboard" 
              className="w-full sm:w-auto px-8 py-4 rounded-full glass-card text-white font-semibold text-lg hover:bg-white/10 transition-all"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-32 w-full max-w-6xl mx-auto">
          <div className="glass-card p-8 rounded-2xl flex flex-col gap-4 transform transition-all hover:-translate-y-2 hover:border-indigo-500/30">
            <div className="w-12 h-12 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 text-2xl">
              🔒
            </div>
            <h3 className="text-xl font-semibold text-white">Password Protected</h3>
            <p className="text-gray-400 leading-relaxed">Secure your sensitive files with strong passwords. Only those with the key can access your data.</p>
          </div>
          
          <div className="glass-card p-8 rounded-2xl flex flex-col gap-4 transform transition-all hover:-translate-y-2 hover:border-purple-500/30">
            <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 text-2xl">
              ⏳
            </div>
            <h3 className="text-xl font-semibold text-white">Auto-Expiring Links</h3>
            <p className="text-gray-400 leading-relaxed">Set expiration dates or maximum download limits to ensure your files don&apos;t live on the internet forever.</p>
          </div>

          <div className="glass-card p-8 rounded-2xl flex flex-col gap-4 transform transition-all hover:-translate-y-2 hover:border-pink-500/30">
            <div className="w-12 h-12 rounded-full bg-pink-500/20 flex items-center justify-center text-pink-400 text-2xl">
              📱
            </div>
            <h3 className="text-xl font-semibold text-white">Instant QR Codes</h3>
            <p className="text-gray-400 leading-relaxed">Generate scannable QR codes for your share links instantly, perfect for printed materials and physical sharing.</p>
          </div>
        </div>
      </main>

      <footer className="mt-auto py-8 text-center text-gray-500 text-sm z-10 border-t border-white/5 bg-black/20 backdrop-blur-md">
        © {new Date().getFullYear()} File2QR. All rights reserved.
      </footer>
    </div>
  );
}
