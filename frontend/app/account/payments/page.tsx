"use client";
import { useEffect, useState } from 'react';
import { WalletAPI, WalletBalance, PaymentItem } from '@/lib/api';

export default function PaymentsPage() {
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [payments, setPayments] = useState<PaymentItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    const load = async () => {
      try {
        const [b, p]: any = await Promise.all([
          WalletAPI.balance(),
          WalletAPI.transactions()
        ]);
        if (ignore) return;
        setBalance(b);
        setPayments(p.items || []);
      } catch (e: any) {
        if (!ignore) setError(e.message || 'Ошибка загрузки оплат');
      }
    };
    load();
    return () => { ignore = true; };
  }, []);

  return (
    <div>
      <h1>Оплаты и кошелёк</h1>
      {error && <p className="form-error">{error}</p>}
      {!balance ? <p>Загрузка баланса...</p> : (
        <div style={{ marginBottom: 16 }}>
          <p><strong>Доступно:</strong> {balance.available_balance?.toFixed?.(2)} {balance.currency || '₽'}</p>
          {typeof balance.bonus_balance === 'number' && <p><strong>Бонусы:</strong> {balance.bonus_balance.toFixed?.(2)} {balance.currency || '₽'}</p>}
          {typeof balance.balance === 'number' && <p><strong>Основной баланс:</strong> {balance.balance.toFixed?.(2)} {balance.currency || '₽'}</p>}
        </div>
      )}
      {!payments ? <p>Загрузка платежей...</p> : (
        <div>
          <h2 style={{ margin: '16px 0 8px' }}>Недавние платежи</h2>
          {payments.length === 0 ? <p>Пока нет платежей</p> : (
            <ul style={{ paddingLeft: 16 }}>
              {payments.slice(0, 10).map(p => (
                <li key={p.id} style={{ marginBottom: 6 }}>
                  {new Date(p.created_at || '').toLocaleString()} · {p.amount?.toFixed?.(2)} {p.currency || '₽'} · {p.status}
                  {p.order_id ? <> · <a className="nav-link" href={`/account/orders?orderId=${p.order_id}`}>заказ</a></> : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}


