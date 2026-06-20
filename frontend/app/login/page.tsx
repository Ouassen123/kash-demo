'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { setAuthUser } from '@/lib/auth-context';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleDevLogin(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/dev-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `HTTP ${res.status}`);
      }

      const data = await res.json();
      const token: string = data.access_token;
      const userObj = data.user;

      setAuthUser({
        id: userObj.id,
        email: userObj.email,
        display_name: userObj.display_name ?? null,
        avatar_url: userObj.avatar_url ?? null,
        is_admin: userObj.is_admin ?? false,
        is_active: true,
      }, token);

      window.location.href = userObj.is_admin ? '/admin' : '/';
    } catch (err: any) {
      setError(`Connexion échouée : ${err.message ?? 'Vérifiez vos identifiants'}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(91,129,255,0.25),_rgba(4,8,20,0.9))]">
      <div className="w-full max-w-sm rounded-2xl border border-white/10 bg-white/5 p-8 space-y-6 backdrop-blur">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold text-white">KASH Platform</h1>
          <p className="text-sm text-white/60">Connectez-vous pour accéder à votre espace</p>
        </div>

        <form onSubmit={handleDevLogin} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs text-white/60 uppercase tracking-wider">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="dev.student@kash.local"
              className="w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/30 focus:border-indigo-400/60 focus:outline-none"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs text-white/60 uppercase tracking-wider">Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/30 focus:border-indigo-400/60 focus:outline-none"
            />
          </div>

          {error && <p className="text-sm text-rose-300 bg-rose-500/10 rounded-xl px-3 py-2">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-indigo-500 py-3 text-sm font-semibold text-white hover:bg-indigo-400 transition disabled:opacity-60"
          >
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <div className="border-t border-white/10 pt-4">
          <p className="text-xs text-white/40 text-center">Mode développement — pas de Firebase requis</p>
          <div className="mt-2 flex flex-col gap-1">
            <button onClick={() => setEmail('dev.student@kash.local')} className="text-xs text-indigo-300 hover:text-indigo-200 text-center">
              → Candidat test : dev.student@kash.local
            </button>
            <button onClick={() => setEmail('admin@kash.local')} className="text-xs text-amber-300 hover:text-amber-200 text-center">
              → Admin test : admin@kash.local
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
