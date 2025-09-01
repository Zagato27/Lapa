"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function AccountLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const items = [
    { href: '/account', label: 'Дашборд' },
    { href: '/account/profile', label: 'Профиль' },
    { href: '/account/pets', label: 'Мои питомцы' },
    { href: '/account/orders', label: 'Заказы и история' },
    { href: '/account/payments', label: 'Оплаты и кошелёк' },
    { href: '/account/chat', label: 'Чат' },
    { href: '/account/settings', label: 'Настройки' },
  ];
  return (
    <div className="container account">
      <aside className="account-nav">
        {items.map((i) => (
          <Link key={i.href} href={i.href} className={`account-nav-link${pathname === i.href ? ' active' : ''}`}>{i.label}</Link>
        ))}
      </aside>
      <section className="account-content">
        {children}
      </section>
    </div>
  );
}


