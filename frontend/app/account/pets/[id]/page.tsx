"use client";
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { PetsAPI, Pet } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export default function PetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const petId = String(params?.id || '');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pet, setPet] = useState<Pet | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await PetsAPI.get(petId);
        if (!mounted) return;
        setPet(data.pet);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message || 'Ошибка загрузки');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [petId]);

  if (loading) return <main className="page container"><p>Загрузка...</p></main>;
  if (error) return <main className="page container"><p>Ошибка: {error}</p></main>;
  if (!pet) return <main className="page container"><p>Питомец не найден</p></main>;

  const sections: { title: string; rows: Array<[string, string | undefined | null]> }[] = [
    { title: 'Общее', rows: [
      ['Имя', pet.name],
      ['Порода', pet.breed],
      ['Пол', pet.gender === 'male' ? 'Мальчик' : pet.gender === 'female' ? 'Девочка' : undefined],
      ['Возраст', pet.age_years ? `${pet.age_years} лет${pet.age_months ? ` ${pet.age_months} мес.` : ''}` : undefined],
      ['Вес', pet.weight_kg ? `${pet.weight_kg} кг` : undefined],
      ['Стерилизация/кастрация', pet.is_neutered ? 'Да' : undefined],
    ]},
  ];

  return (
    <main className="page container">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1>{pet.name}</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" className="icon-btn" aria-label="Редактировать" onClick={() => router.push(`/account/pets/${pet.id}/edit`)}>
            <span aria-hidden="true" style={{ filter: 'grayscale(100%) brightness(0) invert(1)' }}>✏️</span>
          </button>
          <Button onClick={() => router.push(`/account/orders/new?petId=${pet.id}`)}>Погулять</Button>
        </div>
      </div>

      <div className="services-grid" style={{ marginTop: 16, gridTemplateColumns: '1fr' }}>
        <Card title="Общее">
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
            {pet.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={pet.avatar_url} alt={pet.name} style={{ width: 96, height: 96, objectFit: 'cover', borderRadius: 8 }} />
            ) : (
              <div style={{ width: 96, height: 96, borderRadius: 8, background: 'var(--sand-300)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🐶</div>
            )}
          </div>
          <div className="field-grid">
            {sections[0].rows
              .filter(([, v]) => v != null && String(v).trim() !== '')
              .map(([k, v]) => (
                <div key={k} style={{display: 'contents'}}>
                  <div className="field-label">{k}</div>
                  <div className="field-value">{v as string}</div>
                </div>
              ))}
          </div>
        </Card>

        {/* Заглушки для следующих секций (Инструкции по уходу, Здоровье, История услуг и отчёты) */}
        <Card title="Инструкции по уходу"><p>Добавим в следующем шаге (MVP).</p></Card>
        <Card title="Здоровье"><p>Добавим в следующем шаге (MVP).</p></Card>
        <Card title="История услуг и отчёты"><p>Добавим в следующем шаге (MVP).</p></Card>
      </div>
    </main>
  );
}


