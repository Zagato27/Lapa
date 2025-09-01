"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export default function ProfilePage() {
  const { user, loading, refreshProfile, updateProfile, logout } = useAuth();
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '', avatar_url: '', bio: '' });

  useEffect(() => {
    if (user) {
      setForm({
        first_name: (user as any)?.first_name || '',
        last_name: (user as any)?.last_name || '',
        phone: (user as any)?.phone || '',
        avatar_url: (user as any)?.avatar_url || '',
        bio: (user as any)?.bio || '',
      });
    }
  }, [user]);

  if (loading) return <main className="page container"><p>Загрузка...</p></main>;
  if (!user) { router.replace('/login'); return null; }

  return (
    <main className="page container">
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginBottom: 12 }}>
        {!editing ? (
          <>
            <Button onClick={() => setEditing(true)}>Изменить</Button>
            <Button onClick={() => logout().then(() => router.push('/'))}>Выйти</Button>
          </>
        ) : null}
      </div>
      {!editing ? (
        <div className="services-grid" style={{ marginTop: 8 }}>
          <Card title="Email">
            <div>{user?.email || '—'}</div>
          </Card>
          <Card title="Имя">
            <div>{((user as any)?.first_name || '—') + ' ' + ((user as any)?.last_name || '')}</div>
          </Card>
          <Card title="Телефон">
            <div>{(user as any)?.phone || '—'}</div>
          </Card>
          <Card title="О себе">
            <div>{(user as any)?.bio || '—'}</div>
          </Card>
        </div>
      ) : (
        <form className="form" onSubmit={async (e) => {
          e.preventDefault();
          setSaving(true);
          try {
            await updateProfile(form);
            setEditing(false);
          } finally {
            setSaving(false);
          }
        }}>
          <label className="form-label">Имя
            <input className="form-input" value={form.first_name} onChange={e => setForm(v => ({ ...v, first_name: e.target.value }))} />
          </label>
          <label className="form-label">Фамилия
            <input className="form-input" value={form.last_name} onChange={e => setForm(v => ({ ...v, last_name: e.target.value }))} />
          </label>
          <label className="form-label">Телефон
            <input className="form-input" value={form.phone} onChange={e => setForm(v => ({ ...v, phone: e.target.value }))} />
          </label>
          <label className="form-label">Avatar URL
            <input className="form-input" value={form.avatar_url} onChange={e => setForm(v => ({ ...v, avatar_url: e.target.value }))} />
          </label>
          <label className="form-label">О себе
            <input className="form-input" value={form.bio} onChange={e => setForm(v => ({ ...v, bio: e.target.value }))} />
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button disabled={saving} type="submit">Сохранить</Button>
            <Button type="button" variant="secondary" onClick={() => { setEditing(false); setForm({
              first_name: (user as any)?.first_name || '',
              last_name: (user as any)?.last_name || '',
              phone: (user as any)?.phone || '',
              avatar_url: (user as any)?.avatar_url || '',
              bio: (user as any)?.bio || '',
            }); }}>Отмена</Button>
          </div>
        </form>
      )}
    </main>
  );
}
