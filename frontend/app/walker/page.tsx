"use client";
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { OrdersAPI, Order, WalletAPI, WalletBalance } from '@/lib/api';

function IncomingRequests() {
  const [items, setItems] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    const load = async () => {
      try {
        const res = await OrdersAPI.pendingForWalker();
        if (!ignore) setItems(res.orders || []);
      } catch (e: any) {
        if (!ignore) setError(e.message || 'Ошибка загрузки');
      }
    };
    load();
    const id = window.setInterval(load, 15000);
    return () => { ignore = true; window.clearInterval(id); };
  }, []);

  if (error) return <p className="form-error">{error}</p>;
  if (!items) return <p>Загрузка...</p>;
  if (!items.length) return <p>Нет входящих запросов</p>;

  return (
    <ul style={{ paddingLeft: 16, margin: 0 }}>
      {items.slice(0, 5).map((o) => (
        <li key={o.id} style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <strong>{o.scheduled_at ? new Date(o.scheduled_at).toLocaleString() : '—'}</strong>
              {o.address ? ` · ${o.address}` : ''}
              {o.total_price ? ` · цена: ${o.total_price}` : ''}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button onClick={() => OrdersAPI.confirm(o.id).then(() => window.location.reload())}>Принять</Button>
              <Button variant="secondary" onClick={() => { /* отклонение MVP можно пропустить */ }}>Отклонить</Button>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

function ActiveOrders() {
  const [items, setItems] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    const load = async () => {
      try {
        const res: any = await OrdersAPI.list();
        if (ignore) return;
        const orders: Order[] = res.items || [];
        const active = orders.filter((o) => ['confirmed','in_progress','walking','started','active'].includes(String(o.status)));
        setItems(active);
      } catch (e: any) {
        if (!ignore) setError(e.message || 'Ошибка загрузки');
      }
    };
    load();
    const id = window.setInterval(load, 15000);
    return () => { ignore = true; window.clearInterval(id); };
  }, []);

  if (error) return <p className="form-error">{error}</p>;
  if (!items) return <p>Загрузка...</p>;
  if (!items.length) return <p>Нет активных заказов</p>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map((o) => (
        <div key={o.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <strong>{o.status}</strong> · {o.address || '—'}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {o.status === 'confirmed' && <Button onClick={() => OrdersAPI.startWalk(o.id).then(() => window.location.reload())}>Старт</Button>}
            {['in_progress','walking','started','active'].includes(String(o.status)) && (
              <Button onClick={() => OrdersAPI.completeWalk(o.id).then(() => window.location.reload())}>Финиш</Button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function QuickStatus() {
  // MVP: локальный переключатель; позже — синхронизация с user-service
  const [status, setStatus] = useState<'available'|'busy'|'break'>('available');
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8, width: '100%', fontSize: '0.9em' }}>
      <Button
        type="button"
        className="btn-sm"
        variant={status === 'available' ? 'primary' : 'secondary'}
        aria-pressed={status === 'available'}
        onClick={() => setStatus('available')}
      >
        Доступен
      </Button>
      <Button
        type="button"
        className="btn-sm"
        variant={status === 'busy' ? 'primary' : 'secondary'}
        aria-pressed={status === 'busy'}
        onClick={() => setStatus('busy')}
      >
        Занят
      </Button>
      <Button
        type="button"
        className="btn-sm"
        variant={status === 'break' ? 'primary' : 'secondary'}
        aria-pressed={status === 'break'}
        onClick={() => setStatus('break')}
      >
        Перерыв
      </Button>
    </div>
  );
}

function BalanceCard() {
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let ignore = false;
    WalletAPI.balance().then(setBalance).catch((e) => !ignore && setError(e.message || 'Ошибка'));
    return () => { ignore = true; };
  }, []);
  if (error) return <p className="form-error">{error}</p>;
  if (!balance) return <p>Загрузка...</p>;
  return <p><strong>Доступно:</strong> {balance.available_balance} {balance.currency || '₽'}</p>;
}

function ProfileCard() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#eee', overflow: 'hidden' }}>
        {user.avatar_url ? <img src={user.avatar_url} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : null}
      </div>
      <div>
        <p style={{ margin: 0 }}><strong>{user.first_name} {user.last_name}</strong></p>
        <p style={{ margin: 0 }}>{user.email} · {user.phone}</p>
        {typeof (user as any)?.hourly_rate !== 'undefined' && (user as any)?.hourly_rate !== null && (
          <p style={{ margin: 0 }}>Ставка: {(user as any).hourly_rate} ₽/ч</p>
        )}
      </div>
    </div>
  );
}

export default function WalkerDashboardPage() {
  const { user, loading, refreshProfile } = useAuth();
  const router = useRouter();
  const [refreshed, setRefreshed] = useState(false);

  useEffect(() => {
    const access = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (access) {
      refreshProfile().catch(() => {}).finally(() => setRefreshed(true));
    } else {
      setRefreshed(true);
    }
  }, []);

  useEffect(() => {
    if (refreshed && !loading) {
      if (!user) router.replace('/login');
      else if (user.role !== 'walker') router.replace('/account');
    }
  }, [refreshed, loading, user, router]);

  if (loading || !refreshed) return <main className="page container"><p>Загрузка...</p></main>;
  if (!user || user.role !== 'walker') return null;

  return (
    <main>
      <div className="services-grid" style={{ marginTop: 16 }}>
        <Card title="Профиль" subtitle="Краткая информация" className="card-link" style={{ gridColumn: '1 / -1' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 16, alignItems: 'center' }}>
            <div style={{ width: 72, height: 72, borderRadius: '50%', background: '#eee', overflow: 'hidden' }}>
              {user.avatar_url ? <img src={user.avatar_url} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : null}
            </div>
            <div>
              <p style={{ margin: 0, fontSize: 18 }}><strong>{user.first_name} {user.last_name}</strong></p>
              <p style={{ margin: 0, opacity: .8 }}>{user.email} · {user.phone}</p>
            </div>
            <div style={{ justifySelf: 'end', textAlign: 'right' }}>
              {(user as any)?.hourly_rate != null && <p style={{ margin: 0, fontWeight: 700 }}>{(user as any).hourly_rate} ₽/ч</p>}
              <a href="/walker/profile" className="btn btn-secondary" style={{ display: 'inline-flex', padding: '8px 12px', marginTop: 6 }}>Редактировать</a>
            </div>
          </div>
        </Card>

        <Card title="Входящие запросы" subtitle="SLA на принятие">
          <IncomingRequests />
        </Card>
        <Card title="Активные заказы" subtitle="Старт/Пауза/Финиш">
          <ActiveOrders />
        </Card>
        <Card title="Быстрый статус">
          <QuickStatus />
        </Card>
        <Card title="Баланс" subtitle="Ожидаемые выплаты">
          <BalanceCard />
        </Card>
      </div>
    </main>
  );
}


