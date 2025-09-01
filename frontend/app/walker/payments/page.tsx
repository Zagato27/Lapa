"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';
import { WalletAPI, WalletBalance, PaymentItem } from '@/lib/api';
import { Button } from '@/components/ui/Button';

export default function WalkerPaymentsPage() {
  const { user, loading, refreshProfile } = useAuth();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [tx, setTx] = useState<PaymentItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const access = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (access) {
      refreshProfile().catch(() => {}).finally(() => setReady(true));
    } else {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    if (ready && !loading) {
      if (!user) router.replace('/login');
      else if (user.role !== 'walker') router.replace('/account');
    }
  }, [ready, loading, user, router]);

  useEffect(() => {
    if (!user || user.role !== 'walker') return;
    let ignore = false;
    const load = async () => {
      try {
        const b = await WalletAPI.balance();
        const t = await WalletAPI.transactions();
        if (ignore) return;
        setBalance(b);
        setTx(t.items || []);
      } catch (e: any) {
        if (!ignore) setError(e.message || 'Ошибка загрузки');
      }
    };
    load();
    return () => { ignore = true; };
  }, [user]);

  if (loading || !ready) return <main className="page container"><p>Загрузка...</p></main>;
  if (!user || user.role !== 'walker') return null;

  return (
    <main>
      <h1>Выплаты</h1>
      {error && <div className="form-error">{error}</div>}
      <section style={{ marginTop: 16 }}>
        <h2>Баланс</h2>
        {!balance ? <p>Загрузка...</p> : (
          <p><strong>Доступно:</strong> {balance.available_balance} {balance.currency || '₽'}</p>
        )}
        <div style={{ display: 'flex', gap: 8 }}>
          <Button disabled>Запросить выплату (скоро)</Button>
          <Button variant="secondary" disabled>Привязать способ выплат (скоро)</Button>
        </div>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>История операций</h2>
        {!tx ? <p>Загрузка...</p> : !tx.length ? <p>Нет операций</p> : (
          <ul style={{ paddingLeft: 16, margin: 0 }}>
            {tx.slice(0, 20).map((p) => (
              <li key={p.id} style={{ marginBottom: 6 }}>
                <strong>{p.status}</strong> · {p.amount} {p.currency || '₽'} · {p.created_at ? new Date(p.created_at).toLocaleString() : ''}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}


