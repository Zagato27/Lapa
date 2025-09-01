"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';

export default function WalkerLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = [
    { href: '/walker', label: 'Дашборд' },
    { href: '/walker/orders', label: 'Заказы' },
    { href: '/walker/payments', label: 'Выплаты' },
    { href: '/walker/profile', label: 'Профиль' },
  ];
  return (
    <div className="container account">
      <aside className="account-nav">
        {items.map((i) => (
          <Link key={i.href} href={i.href} className={`account-nav-link${pathname === i.href ? ' active' : ''}`}>{i.label}</Link>
        ))}
      </aside>
      <section className="account-content" style={{ position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 12, marginBottom: 12 }}>
          {typeof (user as any)?.hourly_rate !== 'undefined' && (user as any)?.hourly_rate !== null && (
            <span style={{ fontSize: 14, color: 'var(--color-muted)' }}>{(user as any).hourly_rate} ₽/ч</span>
          )}
          <div style={{ width: 40, height: 40, borderRadius: '50%', background: '#eee', overflow: 'hidden' }}>
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : null}
          </div>
        </div>
        {children}
      </section>
    </div>
  );
}


