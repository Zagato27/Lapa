"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';
import { OrdersAPI, Order } from '@/lib/api';
import { Button } from '@/components/ui/Button';

export default function WalkerOrdersPage() {
  const { user, loading, refreshProfile } = useAuth();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [pending, setPending] = useState<Order[] | null>(null);
  const [active, setActive] = useState<Order[] | null>(null);
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
        const p = await OrdersAPI.pendingForWalker();
        const res: any = await OrdersAPI.list();
        if (ignore) return;
        setPending(p.orders || []);
        const items: Order[] = res.items || [];
        setActive(items.filter((o) => ['confirmed','in_progress','walking','started','active'].includes(String(o.status))));
      } catch (e: any) {
        if (!ignore) setError(e.message || 'Ошибка загрузки');
      }
    };
    load();
    const id = window.setInterval(load, 15000);
    return () => { ignore = true; window.clearInterval(id); };
  }, [user]);

  if (loading || !ready) return <main className="page container"><p>Загрузка...</p></main>;
  if (!user || user.role !== 'walker') return null;

  return (
    <main>
      <h1>Заказы</h1>
      {error && <div className="form-error">{error}</div>}
      <section style={{ marginTop: 16 }}>
        <h2>Входящие</h2>
        {!pending ? <p>Загрузка...</p> : !pending.length ? <p>Нет входящих запросов</p> : (
          <ul style={{ paddingLeft: 16, margin: 0 }}>
            {pending.map((o) => (
              <li key={o.id} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <strong>{o.scheduled_at ? new Date(o.scheduled_at).toLocaleString() : '—'}</strong>
                    {o.address ? ` · ${o.address}` : ''}
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <Button onClick={() => OrdersAPI.confirm(o.id).then(() => window.location.reload())}>Принять</Button>
                    <Button variant="secondary" onClick={() => { /* отклонить (MVP: нет эндпоинта) */ }}>Отклонить</Button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Активные</h2>
        {!active ? <p>Загрузка...</p> : !active.length ? <p>Нет активных заказов</p> : (
          <ul style={{ paddingLeft: 16, margin: 0 }}>
            {active.map((o) => (
              <li key={o.id} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <strong>{o.status}</strong>
                    {o.address ? ` · ${o.address}` : ''}
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {o.status === 'confirmed' && <Button onClick={() => OrdersAPI.startWalk(o.id).then(() => window.location.reload())}>Старт</Button>}
                    {['in_progress','walking','started','active'].includes(String(o.status)) && (
                      <Button onClick={() => OrdersAPI.completeWalk(o.id).then(() => window.location.reload())}>Финиш</Button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}


