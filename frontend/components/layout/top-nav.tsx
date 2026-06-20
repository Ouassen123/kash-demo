'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { Shield, LogOut, ChevronDown } from 'lucide-react';
import { useState } from 'react';

export function TopNav() {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  if (pathname === '/login') return null;

  const initials = user
    ? (user.display_name ?? user.email).slice(0, 2).toUpperCase()
    : '?';

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-[#040814]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 lg:px-0">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-sm font-bold tracking-wider text-white">KASH</span>
          <span className="hidden text-xs text-white/40 sm:inline">Intelligence Platform</span>
        </Link>

        <nav className="flex items-center gap-2">
          {!loading && user?.is_admin && (
            <Link
              href="/admin"
              className="flex items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-300 hover:bg-amber-500/20 transition"
            >
              <Shield size={12} /> Admin
            </Link>
          )}

          {!loading && !user?.is_admin && (
            <Link
              href="/kash/start"
              className="rounded-full bg-indigo-500 px-4 py-1.5 text-xs font-semibold text-white hover:bg-indigo-400 transition"
            >
              Démarrer KASH
            </Link>
          )}

          {loading ? (
            <div className="h-8 w-24 animate-pulse rounded-full bg-white/10" />
          ) : user ? (
            <div className="relative">
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-2 rounded-full border border-white/15 px-3 py-1.5 hover:bg-white/10 transition"
              >
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500 text-[10px] font-bold text-white">
                  {initials}
                </div>
                <span className="text-xs text-white/80 hidden sm:inline">
                  {user.display_name ?? user.email.split('@')[0]}
                </span>
                {user.is_admin && (
                  <span className="text-[9px] text-amber-300 hidden sm:inline">· Admin</span>
                )}
                <ChevronDown size={12} className="text-white/40" />
              </button>

              {menuOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                  <div className="absolute right-0 top-full mt-2 z-20 w-48 rounded-xl border border-white/10 bg-[#0a0f1e] shadow-2xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-white/10">
                      <p className="text-xs font-medium text-white truncate">{user.display_name ?? user.email.split('@')[0]}</p>
                      <p className="text-[10px] text-white/40 truncate">{user.email}</p>
                      {user.is_admin && (
                        <span className="mt-1 inline-block text-[9px] text-amber-300 bg-amber-500/10 rounded px-1.5 py-0.5">🛡 Admin</span>
                      )}
                    </div>
                    <Link
                      href="/profile"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 px-4 py-2.5 text-xs text-white/70 hover:bg-white/5 hover:text-white transition"
                    >
                      Mon profil
                    </Link>
                    {user.is_admin && (
                      <Link
                        href="/admin"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-2 px-4 py-2.5 text-xs text-amber-300 hover:bg-amber-500/10 transition"
                      >
                        <Shield size={12} /> Dashboard Admin
                      </Link>
                    )}
                    <button
                      onClick={() => { setMenuOpen(false); logout(); }}
                      className="flex w-full items-center gap-2 px-4 py-2.5 text-xs text-rose-300 hover:bg-rose-500/10 transition border-t border-white/10"
                    >
                      <LogOut size={12} /> Se déconnecter
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="rounded-full border border-white/20 px-3 py-1.5 text-xs text-white/70 hover:bg-white/10 transition"
            >
              Connexion
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
