'use client';
import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';

export default function AuthPage() {
  const supabase = createClient();
  const router = useRouter();

  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  async function handleMagicLink(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/api/auth/callback`,
      },
    });

    setLoading(false);
    if (error) {
      setError(error.message);
    } else {
      setSent(true);
    }
  }

  async function handleGoogle() {
    setLoading(true);
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/api/auth/callback` },
    });
  }

  if (sent) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center card-surface">
          <div className="text-5xl mb-4">🌿</div>
          <h2 className="font-serif text-2xl text-forest mb-3">Check your email</h2>
          <p className="text-earth/80 leading-relaxed">
            We sent a magic link to <strong>{email}</strong>. Click it to join the wall.
            No password needed, ever.
          </p>
          <button onClick={() => setSent(false)} className="btn-ghost mt-6 text-sm">
            Use a different email
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🌲</div>
          <h1 className="font-serif text-3xl text-forest mb-2">
            {mode === 'signin' ? 'Welcome back' : 'Join the wall'}
          </h1>
          <p className="text-earth/70 text-sm">
            {mode === 'signin'
              ? 'Sign in to add your voice and track your Healing Points.'
              : 'It takes under a minute. No password required.'}
          </p>
        </div>

        <div className="card-surface">
          {/* Google OAuth */}
          <button
            onClick={handleGoogle}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 border border-earth/20 rounded-xl px-4 py-3 text-earth font-medium hover:bg-earth/5 transition-colors mb-5 disabled:opacity-50"
          >
            <svg viewBox="0 0 24 24" className="w-5 h-5" aria-hidden>
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          <div className="flex items-center gap-3 mb-5">
            <div className="flex-1 border-t border-earth/15" />
            <span className="text-earth/40 text-xs">or use email</span>
            <div className="flex-1 border-t border-earth/15" />
          </div>

          {/* Magic Link Form */}
          <form onSubmit={handleMagicLink} className="space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              className="form-input"
              aria-label="Email address"
            />
            {error && (
              <p className="text-red-600 text-sm" role="alert">{error}</p>
            )}
            <button type="submit" disabled={loading || !email} className="btn-primary w-full">
              {loading ? 'Sending...' : mode === 'signin' ? 'Send magic link' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-earth/60 text-xs mt-5">
            {mode === 'signin' ? "Don't have an account? " : 'Already have one? '}
            <button
              onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
              className="text-forest underline underline-offset-2"
            >
              {mode === 'signin' ? 'Join the wall' : 'Sign in'}
            </button>
          </p>
        </div>

        <p className="text-center text-earth/40 text-xs mt-6 px-4">
          By joining, you agree to keep this a kind and honest space.
          Your privacy matters — read our values at busyheadproject.org.
        </p>
      </div>
    </div>
  );
}
