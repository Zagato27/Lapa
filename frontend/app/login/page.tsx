"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';
import { Button } from '@/components/ui/Button';

export default function LoginPage() {
  const { login, loading, refreshProfile } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const loggedUser = await login(email, password);
      const role = loggedUser?.role ?? (await (async () => { try { const u = await refreshProfile(); return u?.role; } catch { return null; } })());
      router.replace(role === 'walker' ? '/walker' : '/account');
    } catch (e: any) {
      setError(e.message || 'Ошибка входа');
    }
  };

  return (
    <main className="page container">
      <h1>Вход</h1>
      <form className="form" onSubmit={onSubmit}>
        {error && <div className="form-error">{error}</div>}
        <label className="form-label">Email
          <input className="form-input" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
        </label>
        <label className="form-label">Пароль
          <input className="form-input" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        </label>
        <Button disabled={loading} type="submit">Войти</Button>
      </form>
    </main>
  );
}


