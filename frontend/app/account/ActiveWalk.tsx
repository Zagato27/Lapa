"use client";
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { OrdersAPI, Order } from '@/lib/api';

const ACTIVE_STATUSES = new Set(['in_progress', 'walking', 'started', 'active']);

export default function ActiveWalk() {
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);

  useEffect(() => {
    let ignore = false;
    const load = async () => {
      try {
        const res: any = await OrdersAPI.list();
        if (ignore) return;
        const items: Order[] = res.items || [];
        const active = items.find((o) => o.status && ACTIVE_STATUSES.has(String(o.status)) ) || null;
        setOrder(active);
      } catch (e: any) {
        if (!ignore) setError(e.message || 'Ошибка загрузки');
      }
    };
    load();
    const id = window.setInterval(load, 15000);
    return () => { ignore = true; window.clearInterval(id); };
  }, []);

  useEffect(() => {
    if (!order) { setElapsedSec(0); return; }
    const id = window.setInterval(() => setElapsedSec((s) => s + 1), 1000);
    return () => window.clearInterval(id);
  }, [order]);

  const elapsedText = useMemo(() => {
    const m = Math.floor(elapsedSec / 60).toString().padStart(2, '0');
    const s = (elapsedSec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }, [elapsedSec]);

  if (error) return <p className="form-error">{error}</p>;
  if (!order) return <p>Нет активной прогулки</p>;

  return (
    <div>
      <p><strong>Статус:</strong> {order.status || '—'} · <strong>Таймер:</strong> {elapsedText}</p>
      <p><strong>Адрес:</strong> {order.address || '—'}</p>
      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <Link className="btn btn-secondary" href={`/account/orders?orderId=${order.id}`}>Детали</Link>
        <Link className="btn" href={`/account/chat?orderId=${order.id}`}>Чат</Link>
      </div>
    </div>
  );
}


