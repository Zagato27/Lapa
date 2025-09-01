"use client";
import { useEffect, useState } from 'react';
import { OrdersAPI, Order } from '@/lib/api';

export default function UpcomingOrders() {
  const [items, setItems] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    OrdersAPI.list()
      .then((res: any) => { if (!ignore) setItems(res.items || []); })
      .catch((e) => { if (!ignore) setError(e.message || 'Ошибка загрузки'); });
    return () => { ignore = true; };
  }, []);

  if (error) return <p className="form-error">{error}</p>;
  if (!items) return <p>Загрузка...</p>;
  if (!items.length) return <p>Нет ближайших заказов</p>;

  return (
    <ul style={{ paddingLeft: 16, margin: 0 }}>
      {items.slice(0, 3).map((o) => (
        <li key={o.id} style={{ marginBottom: 8 }}>
          <strong>{o.scheduled_at ? new Date(o.scheduled_at).toLocaleString() : '—'}</strong>
          {o.address ? ` · ${o.address}` : ''} · статус: {o.status}
        </li>
      ))}
    </ul>
  );
}


