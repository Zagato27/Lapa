"use client";
import Link from 'next/link';
import { useAuth } from '@/app/auth-provider';

export function HeaderAuthControls() {
  const { user } = useAuth();
  return (
    <div style={{ display: 'flex', gap: 12 }}>
      {user ? (
        <Link className="nav-link" href={user.role === 'walker' ? '/walker' : '/account'}>Кабинет</Link>
      ) : (
        <>
          <Link className="nav-link" href="/login">Войти</Link>
          <Link className="nav-link" href="/register">Регистрация</Link>
        </>
      )}
    </div>
  );
}


