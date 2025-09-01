"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import UpcomingOrders from './UpcomingOrders';
import ActiveWalk from './ActiveWalk';

export default function AccountPage() {
  const { user, loading, refreshProfile } = useAuth();
  const router = useRouter();
  const [refreshed, setRefreshed] = useState(false);

  // Всегда пробуем загрузить профиль при заходе на страницу, если есть токен
  useEffect(() => {
    const access = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (access) {
      refreshProfile()
        .catch(() => {})
        .finally(() => setRefreshed(true));
    } else {
      setRefreshed(true);
    }
  }, []);

  // Редиректы после попытки обновления профиля
  useEffect(() => {
    if (refreshed && !loading) {
      if (!user) router.replace('/login');
      else if ((user as any)?.role === 'walker') router.replace('/walker');
    }
  }, [refreshed, loading, user, router]);

  if (loading) return <main className="page container"><p>Загрузка...</p></main>;
  if (!user) return null;

  return (
    <main>

      <div className="services-grid" style={{ marginTop: 16 }}>
        <Card title="Ближайшие заказы" subtitle="Сегодня/завтра" actions={<Button variant="ghost" onClick={() => router.push('/account/orders')}>Все</Button>}>
          <UpcomingOrders />
        </Card>

        <Card title="Быстрый заказ прогулки" subtitle="Адрес, время, длительность">
          <div className="form" style={{ marginTop: 8 }}>
            <input className="form-input" placeholder="Адрес" />
            <input className="form-input" placeholder="Дата и время" />
            <input className="form-input" placeholder="Длительность (мин)" />
            <Button>Заказать прогулку</Button>
          </div>
        </Card>

        <Card title="Активная прогулка" subtitle="Живой трек и таймер">
          <ActiveWalk />
        </Card>

        <Card title="Выгульщики рядом" subtitle="Рейтинг, цена, ETA" actions={<Button variant="ghost" onClick={() => router.push('/account/orders')}>Найти</Button>}>
          <p>Подборка по близости и времени прибытия.</p>
        </Card>
      </div>

      <div style={{ marginTop: 24 }}></div>
    </main>
  );
}


