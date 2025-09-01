"use client";

import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { AuthAPI, AuthTokens, LoginResponse } from '@/lib/api';

type User = {
  id?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  role?: string;
  phone?: string;
  avatar_url?: string;
  bio?: string;
} | null;

type AuthContextType = {
  user: User;
  loading: boolean;
  login: (email: string, password: string) => Promise<any>;
  register: (payload: { email: string; password: string; phone: string; first_name: string; last_name: string; role?: string; }) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<any>;
  updateProfile: (payload: Partial<{ first_name: string; last_name: string; phone: string; avatar_url: string; bio: string; hourly_rate: number }>) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function getTokens() {
  if (typeof window === 'undefined') return { access: null, refresh: null };
  return { access: localStorage.getItem('access_token'), refresh: localStorage.getItem('refresh_token') };
}
function setTokens(tokens?: AuthTokens) {
  if (!tokens) return;
  localStorage.setItem('access_token', tokens.access_token);
  if (tokens.refresh_token) localStorage.setItem('refresh_token', tokens.refresh_token);
}
function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const { access } = getTokens();
    if (!access) {
      setLoading(false);
      return;
    }
    AuthAPI.profile()
      .then((u: any) => setUser((u as any)?.user))
      .catch(() => clearTokens())
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    try {
      const resp: LoginResponse = await AuthAPI.login(email, password);
      setTokens(resp.tokens);
      setUser(resp.user as any);
      return resp.user as any;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (payload: { email: string; password: string; phone: string; first_name: string; last_name: string; role?: string; }) => {
    setLoading(true);
    try {
      await AuthAPI.register(payload);
      const resp: LoginResponse = await AuthAPI.login(payload.email, payload.password);
      setTokens(resp.tokens);
      setUser(resp.user as any);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try { await AuthAPI.logout(); } catch {}
    clearTokens();
    setUser(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    const u = await AuthAPI.profile();
    const nextUser = (u as any)?.user ?? (u as any);
    setUser(nextUser);
    return nextUser;
  }, []);

  const updateProfile = useCallback(async (payload: Partial<{ first_name: string; last_name: string; phone: string; avatar_url: string; bio: string; hourly_rate: number }>) => {
    const updated = await AuthAPI.updateProfile(payload);
    setUser((updated as any)?.user);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshProfile, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}


