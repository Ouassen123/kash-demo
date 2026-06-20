'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { getStoredToken } from '@/lib/auth-context';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

interface ProfileData {
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  is_admin: boolean;
  created_at: string;
  last_login_at: string | null;
}

interface Scores {
  knowledge: number;
  abilities: number;
  skills: number;
  overall: number;
}

export default function ProfilePage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [scores, setScores] = useState<Scores | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('kash_user');
    if (!stored) router.push('/login');
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem('kash_user');
    if (!stored) return;
    const token = getStoredToken();
    const headers = { Authorization: `Bearer ${token}` };

    fetch(`${API_BASE}/auth/me`, { headers }).then(r => r.json()).then(d => {
      setProfile(d);
      setDisplayName(d.display_name ?? '');
    });

    fetch(`${API_BASE}/intelligence/profile`, { headers }).then(r => r.json()).then(d => {
      const s = d.current_kash_score ?? {};
      setScores({
        knowledge: Math.round(s.knowledge ?? 0),
        abilities: Math.round(s.abilities ?? 0),
        skills: Math.round(s.skills ?? 0),
        overall: Math.round(s.overall ?? 0),
      });
    });
  }, [user]);

  async function saveProfile() {
    setSaving(true);
    const token = getStoredToken();
    await fetch(`${API_BASE}/auth/me`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ display_name: displayName }),
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  if (loading || !user) return null;

  const initials = (profile?.display_name ?? user.email).slice(0, 2).toUpperCase();

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(91,129,255,0.25),_rgba(4,8,20,0.9))] px-4 py-10">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm text-white/50 hover:text-white">← Dashboard</Link>
        </div>

        {/* Avatar + info */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 flex items-center gap-5">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-500 text-xl font-bold text-white">
            {initials}
          </div>
          <div className="flex-1">
            <p className="text-lg font-semibold text-white">{profile?.display_name ?? user.email}</p>
            <p className="text-sm text-white/50">{user.email}</p>
            <p className="text-xs text-white/30 mt-1">
              {user.is_admin ? '🛡 Admin' : '👤 Candidat'} · Membre depuis {profile?.created_at ? new Date(profile.created_at).toLocaleDateString('fr-FR') : '—'}
            </p>
          </div>
          <button onClick={logout} className="rounded-xl border border-rose-400/30 px-4 py-2 text-xs text-rose-300 hover:bg-rose-500/10 transition">
            Déconnexion
          </button>
        </div>

        {/* KASH Scores */}
        {scores && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 space-y-4">
            <p className="text-xs uppercase tracking-widest text-white/50">Mes scores KASH</p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: 'Global', value: scores.overall, color: 'bg-indigo-500' },
                { label: 'Knowledge', value: scores.knowledge, color: 'bg-emerald-500' },
                { label: 'Abilities', value: scores.abilities, color: 'bg-violet-500' },
                { label: 'Skills', value: scores.skills, color: 'bg-amber-500' },
              ].map(({ label, value, color }) => (
                <div key={label} className="rounded-xl bg-white/5 border border-white/10 p-4 text-center">
                  <p className="text-2xl font-bold text-white">{value}</p>
                  <div className={`mx-auto mt-2 h-1 rounded-full ${color}`} style={{ width: `${value}%` }} />
                  <p className="text-xs text-white/50 mt-2">{label}</p>
                </div>
              ))}
            </div>
            <div className="text-center">
              <Link href="/kash/start" className="inline-flex items-center gap-2 rounded-full bg-indigo-500 px-5 py-2 text-xs font-semibold text-white hover:bg-indigo-400 transition">
                Repasser les tests KASH →
              </Link>
            </div>
          </div>
        )}

        {/* Edit profile */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 space-y-4">
          <p className="text-xs uppercase tracking-widest text-white/50">Modifier le profil</p>
          <div className="space-y-2">
            <label className="text-xs text-white/60">Nom affiché</label>
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white focus:border-indigo-400/60 focus:outline-none"
            />
          </div>
          <button onClick={saveProfile} disabled={saving} className="rounded-xl bg-indigo-500 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-400 transition disabled:opacity-60">
            {saving ? 'Sauvegarde...' : saved ? '✓ Sauvegardé' : 'Sauvegarder'}
          </button>
        </div>
      </div>
    </main>
  );
}
