'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

export interface CurrentUser {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  is_admin: boolean;
  is_active: boolean;
}

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({ user: null, loading: true, logout: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('kash_user');
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
    setLoading(false);
  }, []);

  function logout() {
    localStorage.removeItem('kash_user');
    localStorage.removeItem('kash_token');
    setUser(null);
    window.location.href = '/login';
  }

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function setAuthUser(user: CurrentUser, token: string) {
  localStorage.setItem('kash_user', JSON.stringify(user));
  localStorage.setItem('kash_token', token);
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('kash_token');
}
