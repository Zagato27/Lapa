"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PetsAPI } from '@/lib/api';
import { ALL_BREEDS, SUPPORTED_BREEDS } from '@/lib/breeds';

const BREEDS = ALL_BREEDS;
import { Button } from '@/components/ui/Button';

export default function NewPetPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: '',
    breed: '',
    gender: 'male',
    weight_kg: '' as any,
  });

  return (
    <main className="page container">
      <h1>Добавить питомца</h1>
      <form className="form" onSubmit={async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
          const payload: any = {
            name: form.name,
            breed: form.breed,
            gender: form.gender,
          };
          if (form.weight_kg) payload.weight_kg = parseFloat(form.weight_kg);
          const created = await PetsAPI.create(payload);
          router.replace(`/account/pets/${created.pet.id}`);
        } catch (err) {
          alert('Ошибка сохранения');
        } finally {
          setSaving(false);
        }
      }}>
        <label className="form-label">Имя
          <input className="form-input" value={form.name} onChange={e => setForm(v => ({ ...v, name: e.target.value }))} required />
        </label>
        <label className="form-label">Порода
          <select className="form-input" value={form.breed} onChange={e => setForm(v => ({ ...v, breed: e.target.value }))} required>
            <option value="" disabled>Выберите породу</option>
            {BREEDS.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
        </label>
        <label className="form-label">Пол
          <select className="form-input" value={form.gender} onChange={e => setForm(v => ({ ...v, gender: e.target.value }))}>
            <option value="male">Мальчик</option>
            <option value="female">Девочка</option>
          </select>
        </label>
        <label className="form-label">Вес (кг)
          <input className="form-input" type="number" step="0.1" value={form.weight_kg} onChange={e => setForm(v => ({ ...v, weight_kg: e.target.value }))} />
        </label>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button disabled={saving} type="submit">Сохранить</Button>
          <Button variant="secondary" type="button" onClick={() => router.back()}>Отмена</Button>
        </div>
      </form>
    </main>
  );
}


