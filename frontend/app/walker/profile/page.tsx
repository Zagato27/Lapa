"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';
import { Button } from '@/components/ui/Button';
import { MediaAPI } from '@/lib/api';

export default function WalkerProfilePage() {
  const { user, loading, refreshProfile, updateProfile, logout } = useAuth();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [bio, setBio] = useState('');
  const [hourlyRate, setHourlyRate] = useState<number | ''>('');
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  useEffect(() => {
    const access = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (access) {
      refreshProfile().catch(() => {}).finally(() => setReady(true));
    } else {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    if (ready && !loading) {
      if (!user) router.replace('/login');
      else if (user.role !== 'walker') router.replace('/account');
      else {
        setFirstName(user.first_name || '');
        setLastName(user.last_name || '');
        setPhone(user.phone || '');
        setAvatarUrl(user.avatar_url || '');
        setAvatarPreview(user.avatar_url || null);
        setBio(user.bio || '');
        setHourlyRate((user as any)?.hourly_rate ?? '');
      }
    }
  }, [ready, loading, user, router]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setOk(null);
    try {
      await updateProfile({ first_name: firstName, last_name: lastName, phone, avatar_url: avatarUrl, bio, ...(hourlyRate !== '' ? { hourly_rate: Number(hourlyRate) } : {}) });
      setOk('Профиль обновлён');
    } catch (e: any) {
      setError(e.message || 'Ошибка обновления');
    }
  };

  const onLogout = async () => {
    try {
      await logout();
    } finally {
      router.replace('/login');
    }
  };

  const onPickFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setOk(null);
    setUploading(true);
    try {
      const preview = URL.createObjectURL(file);
      setAvatarPreview(preview);
      const res = await MediaAPI.uploadAvatar(file);
      const rawUrl = res.public_url || res.file_url;
      if (rawUrl) {
        const base = (process.env.NEXT_PUBLIC_MEDIA_BASE_URL && typeof process.env.NEXT_PUBLIC_MEDIA_BASE_URL === 'string')
          ? process.env.NEXT_PUBLIC_MEDIA_BASE_URL.replace(/\/$/, '')
          : (typeof window !== 'undefined' ? `http://${window.location.hostname}:8007` : '');
        const fullUrl = rawUrl.startsWith('http') ? rawUrl : `${base}${rawUrl}`;
        setAvatarUrl(fullUrl);
        // Автосохранение аватара в профиль
        await updateProfile({ avatar_url: fullUrl });
        await refreshProfile();
        setOk('Фото загружено и сохранено');
      } else {
        setOk('Фото загружено');
      }
    } catch (e: any) {
      setError(e.message || 'Ошибка загрузки фото');
    } finally {
      setUploading(false);
    }
  };

  if (loading || !ready) return <main className="page container"><p>Загрузка...</p></main>;
  if (!user || user.role !== 'walker') return null;

  return (
    <main className="page container">
      <h1>Профиль выгульщика</h1>
      {error && <div className="form-error">{error}</div>}
      {ok && <div className="form-success">{ok}</div>}
      <form className="form" onSubmit={onSubmit} style={{ maxWidth: 520, display: 'grid', gap: 16 }}>
        <div className="form-label" style={{ marginBottom: 0 }}>
          <label className="form-label" style={{ marginBottom: 8 }}>Фото выгульщика</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 96, height: 96, borderRadius: '50%', background: '#eee', overflow: 'hidden', flex: '0 0 auto' }}>
              {avatarPreview ? <img src={avatarPreview} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : null}
            </div>
            <div style={{ flex: '1 1 auto' }}>
              <input className="form-input" type="file" accept="image/*" onChange={onPickFile} />
              {uploading && <div style={{ marginTop: 8 }}>Загрузка...</div>}
            </div>
          </div>
        </div>
        <label className="form-label">Имя
          <input className="form-input" value={firstName} onChange={e => setFirstName(e.target.value)} />
        </label>
        <label className="form-label">Фамилия
          <input className="form-input" value={lastName} onChange={e => setLastName(e.target.value)} />
        </label>
        <label className="form-label">Телефон
          <input className="form-input" value={phone} onChange={e => setPhone(e.target.value)} />
        </label>
        <label className="form-label">О себе
          <textarea className="form-input" value={bio} onChange={e => setBio(e.target.value)} rows={4} />
        </label>
        <label className="form-label">Ставка (₽/час)
          <input className="form-input" type="number" min={0} step={50} value={hourlyRate} onChange={e => setHourlyRate(e.target.value === '' ? '' : Number(e.target.value))} />
        </label>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Button type="submit">Сохранить</Button>
          <Button variant="secondary" type="button" onClick={onLogout}>Выйти из аккаунта</Button>
        </div>
      </form>
    </main>
  );
}


