"use client";
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { PetsAPI } from '@/lib/api';
import { ALL_BREEDS, SUPPORTED_BREEDS } from '@/lib/breeds';

const BREEDS = ALL_BREEDS;
import { Button } from '@/components/ui/Button';

export default function EditPetPage() {
  const params = useParams();
  const petId = String(params?.id || '');
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<any>({ name: '', breed: '', gender: 'male', weight_kg: '' });

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await PetsAPI.get(petId);
        if (!mounted) return;
        const p = data.pet as any;
        setForm({
          name: p.name || '',
          breed: p.breed || '',
          gender: p.gender || 'male',
          weight_kg: p.weight_kg ?? '',
        });
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [petId]);

  if (loading) return <main className="page container"><p>Загрузка...</p></main>;

  return (
    <main className="page container">
      <h1>Редактировать питомца</h1>
      <form className="form" onSubmit={async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
          const payload: any = {
            name: form.name,
            breed: form.breed,
            gender: form.gender,
          };
          if (form.weight_kg !== '') payload.weight_kg = parseFloat(form.weight_kg);
          const updated = await PetsAPI.update(petId, payload);
          router.replace(`/account/pets/${updated.pet.id}`);
        } catch (err) {
          alert('Ошибка сохранения');
        } finally {
          setSaving(false);
        }
      }}>
        <label className="form-label">Имя
          <input className="form-input" value={form.name} onChange={e => setForm((v: any) => ({ ...v, name: e.target.value }))} required />
        </label>
        <label className="form-label">Порода
          <select className="form-input" value={form.breed} onChange={e => setForm((v: any) => ({ ...v, breed: e.target.value }))} required>
            <option value="" disabled>Выберите породу</option>
            {BREEDS.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
        </label>
        <label className="form-label">Пол
          <select className="form-input" value={form.gender} onChange={e => setForm((v: any) => ({ ...v, gender: e.target.value }))}>
            <option value="male">Мальчик</option>
            <option value="female">Девочка</option>
          </select>
        </label>
        <label className="form-label">Вес (кг)
          <input className="form-input" type="number" step="0.1" value={form.weight_kg} onChange={e => setForm((v: any) => ({ ...v, weight_kg: e.target.value }))} />
        </label>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button disabled={saving} type="submit">Сохранить</Button>
          <Button variant="secondary" type="button" onClick={() => router.back()}>Отмена</Button>
        </div>
      </form>
    </main>
  );
}


