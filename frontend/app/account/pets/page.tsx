"use client";
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { PetsAPI, Pet } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export default function PetsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pets, setPets] = useState<Pet[]>([]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await PetsAPI.list(1, 20, { refresh: true });
        if (!mounted) return;
        setPets(data.pets || []);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message || 'Ошибка загрузки');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  if (loading) return <main className="page container"><p>Загрузка...</p></main>;
  if (error) return <main className="page container"><p>Ошибка: {error}</p></main>;

  return (
    <main className="page container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Мои питомцы</h1>
        <Button onClick={() => router.push('/account/pets/new')}>Добавить питомца</Button>
      </div>

      {pets.length === 0 ? (
        <div style={{ marginTop: 16 }}>
          <p>Питомцев пока нет.</p>
          <Button onClick={() => router.push('/account/pets/new')}>Добавить первого питомца</Button>
        </div>
      ) : (
        <div className="services-grid" style={{ marginTop: 16 }}>
          {pets.map((p) => (
            <Card key={p.id}
                  title={p.name}
                  subtitle={`${p.breed}${p.age_years ? ` • ${p.age_years} г.` : ''}`}
                  clickable
                  onClick={() => router.push(`/account/pets/${p.id}`)}
                  actions={
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="button" className="icon-btn" aria-label="Редактировать"
                              onClick={(e) => { e.stopPropagation(); router.push(`/account/pets/${p.id}/edit`); }}>
                        <span aria-hidden="true" style={{ filter: 'grayscale(100%) brightness(0) invert(1)' }}>✏️</span>
                      </button>
                      <Button onClick={(e) => { e.stopPropagation(); router.push(`/account/orders?petId=${p.id}`); }}>Погулять</Button>
                    </div>
                  }>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                {p.avatar_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={p.avatar_url} alt={p.name} style={{ width: 72, height: 72, objectFit: 'cover', borderRadius: 8 }} />
                ) : (
                  <div style={{ width: 72, height: 72, borderRadius: 8, background: 'var(--sand-300)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🐶</div>
                )}
                <div>
                  <div style={{ color: 'var(--charcoal-700)' }}>{p.gender === 'male' ? 'Мальчик' : p.gender === 'female' ? 'Девочка' : ''}{p.is_neutered ? ' • стерилизован' : ''}</div>
                  <div style={{ color: 'var(--charcoal-600)' }}>Вес: {p.weight_kg ? `${p.weight_kg} кг` : '—'}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </main>
  );
}



