'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth, getStoredToken } from '@/lib/auth-context';
import { Users, Activity, BarChart3, TrendingUp, Search, Shield, XCircle, CheckCircle, Edit2, Plus, X, Save } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

interface Stats {
  total_candidates: number;
  active_candidates: number;
  assessments_today: number;
  assessments_this_week: number;
  avg_kash_score: number;
}

interface Candidate {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  is_admin: boolean;
  kash_score: number;
  knowledge_score: number;
  abilities_score: number;
  skills_score: number;
  total_assessments: number;
  last_assessment_at: string | null;
  created_at: string;
  last_login_at: string | null;
}

interface ActivityPoint { date: string; count: number; }

function ScoreBadge({ value }: { value: number }) {
  const color = value >= 70 ? 'text-emerald-300' : value >= 40 ? 'text-amber-300' : 'text-rose-300';
  return <span className={`font-semibold ${color}`}>{Math.round(value)}</span>;
}

export default function AdminPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [activity, setActivity] = useState<ActivityPoint[]>([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Candidate | null>(null);
  const [candidateAssessments, setCandidateAssessments] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);
  const [editName, setEditName] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    // Read directly from localStorage to avoid redirect before AuthProvider hydrates
    const stored = localStorage.getItem('kash_user');
    if (!stored) { router.push('/login'); return; }
    try {
      const u = JSON.parse(stored);
      if (!u.is_admin) { router.push('/'); return; }
    } catch { router.push('/login'); }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem('kash_user');
    if (!stored) return;
    let isAdmin = false;
    try { isAdmin = JSON.parse(stored).is_admin; } catch {}
    if (!isAdmin) return;
    const token = getStoredToken();
    const h = { Authorization: `Bearer ${token}` };
    const load = async () => {
      setFetching(true);
      const [sRes, cRes, aRes] = await Promise.all([
        fetch(`${API_BASE}/admin/stats`, { headers: h }),
        fetch(`${API_BASE}/admin/candidates?limit=100`, { headers: h }),
        fetch(`${API_BASE}/admin/activity?days=14`, { headers: h }),
      ]);
      if (sRes.ok) setStats(await sRes.json());
      if (cRes.ok) setCandidates(await cRes.json());
      if (aRes.ok) setActivity(await aRes.json());
      setFetching(false);
    };
    load();
  }, [user]);

  async function loadCandidateDetail(c: Candidate) {
    setSelected(c);
    setEditName(c.display_name);
    setEditMode(false);
    const token = getStoredToken();
    const r = await fetch(`${API_BASE}/admin/candidates/${c.id}/assessments`, { headers: { Authorization: `Bearer ${token}` } });
    if (r.ok) setCandidateAssessments(await r.json());
  }

  async function toggleActive(c: Candidate) {
    const token = getStoredToken();
    const r = await fetch(`${API_BASE}/admin/candidates/${c.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ is_active: !c.is_active }),
    });
    if (r.ok) {
      const updated = (await r.json()).candidate;
      setCandidates(prev => prev.map(x => x.id === c.id ? { ...x, is_active: !c.is_active } : x));
      if (selected?.id === c.id) setSelected({ ...selected, is_active: !c.is_active });
    }
  }

  async function saveName() {
    if (!selected) return;
    const token = getStoredToken();
    const r = await fetch(`${API_BASE}/admin/candidates/${selected.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ display_name: editName }),
    });
    if (r.ok) {
      setCandidates(prev => prev.map(x => x.id === selected.id ? { ...x, display_name: editName } : x));
      setSelected({ ...selected, display_name: editName });
      setEditMode(false);
    }
  }

  async function createCandidate() {
    if (!newEmail.trim()) return;
    setCreating(true);
    setCreateError(null);
    const token = getStoredToken();
    const r = await fetch(`${API_BASE}/admin/candidates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ email: newEmail.trim(), display_name: newName.trim() || null, is_active: true }),
    });
    if (!r.ok) {
      const detail = await r.json().catch(() => ({} as any));
      setCreateError(detail.detail ?? `Erreur création: ${r.status}`);
      setCreating(false);
      return;
    }

    const reload = await fetch(`${API_BASE}/admin/candidates?limit=100`, { headers: { Authorization: `Bearer ${token}` } });
    if (reload.ok) setCandidates(await reload.json());
    setShowCreate(false);
    setNewEmail('');
    setNewName('');
    setCreating(false);
  }


  const filtered = candidates.filter(c =>
    c.email.toLowerCase().includes(search.toLowerCase()) ||
    (c.display_name ?? '').toLowerCase().includes(search.toLowerCase())
  );

  const maxActivity = Math.max(...activity.map(a => a.count), 1);

  if (loading || !user) return null;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(91,129,255,0.15),_rgba(4,8,20,0.95))] flex">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-white/10 bg-white/2 p-5 flex flex-col gap-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-white/40">KASH Admin</p>
          <p className="text-lg font-bold text-white mt-1">Tableau de bord</p>
        </div>
        <nav className="flex flex-col gap-1">
          <Link href="/admin" className="flex items-center gap-2 rounded-xl bg-white/10 px-3 py-2 text-sm text-white">
            <Users size={15} /> Candidats
          </Link>
          <Link href="/" className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-white/60 hover:bg-white/5">
            <BarChart3 size={15} /> Dashboard candidat
          </Link>
        </nav>
        <div className="mt-auto border-t border-white/10 pt-4">
          <p className="text-xs text-white/40">{user.email}</p>
          <p className="text-xs text-amber-300 mt-0.5">🛡 Admin</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6 space-y-6">

        {/* Stats cards */}
        {stats && (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            {[
              { label: 'Candidats total', value: stats.total_candidates, icon: <Users size={16} />, color: 'text-indigo-300' },
              { label: 'Actifs', value: stats.active_candidates, icon: <Users size={16} />, color: 'text-emerald-300' },
              { label: 'Tests aujourd\'hui', value: stats.assessments_today, icon: <Activity size={16} />, color: 'text-violet-300' },
              { label: 'Tests cette semaine', value: stats.assessments_this_week, icon: <TrendingUp size={16} />, color: 'text-amber-300' },
              { label: 'Score KASH moyen', value: `${stats.avg_kash_score}/100`, icon: <BarChart3 size={16} />, color: 'text-rose-300' },
            ].map(({ label, value, icon, color }) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className={`flex items-center gap-1.5 ${color} mb-2`}>{icon}<span className="text-xs">{label}</span></div>
                <p className="text-2xl font-bold text-white">{value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Activity chart */}
        {activity.length > 0 && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <p className="text-xs uppercase tracking-widest text-white/40 mb-4">Activité — 14 derniers jours</p>
            <div className="flex items-end gap-1 h-20">
              {activity.map((a) => (
                <div key={a.date} className="flex-1 flex flex-col items-center gap-1 group">
                  <div
                    className="w-full rounded-t bg-indigo-500/60 hover:bg-indigo-400 transition"
                    style={{ height: `${(a.count / maxActivity) * 100}%`, minHeight: '4px' }}
                    title={`${a.date}: ${a.count} tests`}
                  />
                  <p className="text-[9px] text-white/30 hidden group-hover:block">{a.date.slice(5)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          {/* Candidates table */}
          <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
            <div className="p-4 border-b border-white/10 flex items-center gap-3">
              <p className="text-sm font-semibold text-white flex-1">Candidats ({filtered.length})</p>
              <button onClick={() => setShowCreate(true)} className="flex items-center gap-1 rounded-xl bg-indigo-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-400 transition">
                <Plus size={12} /> Nouveau
              </button>
              <div className="relative">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Rechercher..."
                  className="rounded-xl border border-white/15 bg-white/5 pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-400/60"
                />
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-white/40">
                    <th className="text-left px-4 py-2">Candidat</th>
                    <th className="text-center px-3 py-2">KASH</th>
                    <th className="text-center px-3 py-2">K</th>
                    <th className="text-center px-3 py-2">A</th>
                    <th className="text-center px-3 py-2">S</th>
                    <th className="text-center px-3 py-2">Tests</th>
                    <th className="text-center px-3 py-2">Statut</th>
                    <th className="text-center px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {fetching ? (
                    <tr><td colSpan={8} className="text-center py-8 text-white/30">Chargement...</td></tr>
                  ) : filtered.length === 0 ? (
                    <tr><td colSpan={8} className="text-center py-8 text-white/30">Aucun candidat trouvé</td></tr>
                  ) : filtered.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => loadCandidateDetail(c)}
                      className={`border-b border-white/5 cursor-pointer hover:bg-white/5 transition ${selected?.id === c.id ? 'bg-indigo-500/10' : ''}`}
                    >
                      <td className="px-4 py-3">
                        <p className="text-white font-medium">{c.display_name}</p>
                        <p className="text-white/40">{c.email}</p>
                      </td>
                      <td className="text-center px-3"><ScoreBadge value={c.kash_score} /></td>
                      <td className="text-center px-3 text-white/60">{Math.round(c.knowledge_score)}</td>
                      <td className="text-center px-3 text-white/60">{Math.round(c.abilities_score)}</td>
                      <td className="text-center px-3 text-white/60">{Math.round(c.skills_score)}</td>
                      <td className="text-center px-3 text-white/60">{c.total_assessments}</td>
                      <td className="text-center px-3">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] ${c.is_active ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'}`}>
                          {c.is_active ? 'Actif' : 'Inactif'}
                        </span>
                      </td>
                      <td className="text-center px-3" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => toggleActive(c)}
                          className={`rounded-full p-1 hover:opacity-80 transition ${c.is_active ? 'text-rose-300' : 'text-emerald-300'}`}
                          title={c.is_active ? 'Désactiver' : 'Activer'}
                        >
                          {c.is_active ? <XCircle size={14} /> : <CheckCircle size={14} />}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Candidate detail panel */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 space-y-4">
            {!selected ? (
              <div className="text-center py-8">
                <Users size={32} className="mx-auto text-white/20 mb-2" />
                <p className="text-sm text-white/40">Cliquez sur un candidat pour voir le détail</p>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">
                    {selected.display_name.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1">
                    {editMode ? (
                      <div className="flex items-center gap-1">
                        <input value={editName} onChange={e => setEditName(e.target.value)}
                          className="flex-1 rounded-lg border border-white/20 bg-white/5 px-2 py-1 text-xs text-white focus:outline-none"
                        />
                        <button onClick={saveName} className="text-emerald-300 hover:opacity-80"><Save size={13} /></button>
                        <button onClick={() => setEditMode(false)} className="text-white/40 hover:opacity-80"><X size={13} /></button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1">
                        <p className="text-sm font-semibold text-white">{selected.display_name}</p>
                        <button onClick={() => setEditMode(true)} className="text-white/30 hover:text-white transition"><Edit2 size={11} /></button>
                      </div>
                    )}
                    <p className="text-xs text-white/40">{selected.email}</p>
                  </div>
                  <button onClick={() => toggleActive(selected)}
                    className={`rounded-full border px-2 py-1 text-[10px] transition ${
                      selected.is_active ? 'border-rose-400/30 text-rose-300 hover:bg-rose-500/10' : 'border-emerald-400/30 text-emerald-300 hover:bg-emerald-500/10'
                    }`}>
                    {selected.is_active ? 'Désactiver' : 'Activer'}
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  {[
                    { l: 'KASH', v: selected.kash_score },
                    { l: 'Knowledge', v: selected.knowledge_score },
                    { l: 'Abilities', v: selected.abilities_score },
                    { l: 'Skills', v: selected.skills_score },
                  ].map(({ l, v }) => (
                    <div key={l} className="rounded-xl bg-white/5 border border-white/10 p-3">
                      <p className="text-[10px] text-white/40">{l}</p>
                      <p className="text-lg font-bold text-white">{Math.round(v)}<span className="text-xs text-white/30">/100</span></p>
                      <div className="mt-1 h-1 rounded-full bg-white/10">
                        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.min(v, 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="space-y-1">
                  <p className="text-[10px] uppercase tracking-wider text-white/40">Infos</p>
                  <p className="text-xs text-white/60">Inscrit : {new Date(selected.created_at).toLocaleDateString('fr-FR')}</p>
                  <p className="text-xs text-white/60">Dernière connexion : {selected.last_login_at ? new Date(selected.last_login_at).toLocaleDateString('fr-FR') : '—'}</p>
                  <p className="text-xs text-white/60">Dernier test : {selected.last_assessment_at ? new Date(selected.last_assessment_at).toLocaleDateString('fr-FR') : '—'}</p>
                  <p className="text-xs text-white/60">Total tests : {selected.total_assessments}</p>
                </div>

                {candidateAssessments.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[10px] uppercase tracking-wider text-white/40">Historique assessments</p>
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {candidateAssessments.map((a) => (
                        <div key={a.id} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                          <div>
                            <p className="text-xs text-white capitalize">{a.type}</p>
                            <p className="text-[10px] text-white/40">{new Date(a.created_at).toLocaleDateString('fr-FR')}</p>
                          </div>
                          <ScoreBadge value={a.score} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>

      {/* Create candidate modal */}
      {showCreate && (
        <>
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" onClick={() => setShowCreate(false)} />
          <div className="fixed left-1/2 top-1/2 z-50 w-96 -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-white/15 bg-[#0a0f1e] p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-semibold text-white">Nouveau candidat</p>
              <button onClick={() => setShowCreate(false)} className="text-white/40 hover:text-white"><X size={16} /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-white/50">Email <span className="text-white/30">(servira d'identifiant de connexion)</span></label>
                <input value={newEmail} onChange={e => setNewEmail(e.target.value)}
                  placeholder="candidat@example.com"
                  className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs text-white focus:border-indigo-400/60 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs text-white/50">Nom affiché <span className="text-white/30">(optionnel)</span></label>
                <input value={newName} onChange={e => setNewName(e.target.value)}
                  placeholder="Prénom Nom"
                  className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs text-white focus:border-indigo-400/60 focus:outline-none"
                />
              </div>

              {createError && (
                <div className="rounded-xl bg-rose-500/10 border border-rose-400/20 px-3 py-2 text-xs text-rose-200/90">
                  {createError}
                </div>
              )}

              {/* Login info box */}
              <div className="rounded-xl bg-indigo-500/10 border border-indigo-400/20 px-3 py-2.5 text-xs text-indigo-200/80 space-y-0.5">
                <p className="font-medium text-indigo-300">ℹ️ Connexion sans mot de passe</p>
                <p>Le candidat se connecte sur <span className="font-mono text-white/70">/login</span> avec son email uniquement. Aucun mot de passe n'est requis.</p>
              </div>
              <button onClick={createCandidate} disabled={creating || !newEmail.trim()}
                className="w-full rounded-xl bg-indigo-500 py-2 text-xs font-semibold text-white hover:bg-indigo-400 transition disabled:opacity-50">
                {creating ? 'Création...' : 'Créer le candidat'}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
