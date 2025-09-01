"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth-provider';
import { Button } from '@/components/ui/Button';

export default function RegisterPage() {
  const { register, loading } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ email: '', password: '', phone: '', first_name: '', last_name: '', role: 'client' });
  const [error, setError] = useState<string | null>(null);

  const onChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await register(form);
      router.push('/account');
    } catch (e: any) {
      setError(e.message || 'Ошибка регистрации');
    }
  };

  return (
    <main className="page container">
      <h1>Регистрация</h1>
      <form className="form" onSubmit={onSubmit}>
        {error && <div className="form-error">{error}</div>}
        <label className="form-label">Email
          <input className="form-input" name="email" type="email" value={form.email} onChange={onChange} required />
        </label>
        <label className="form-label">Пароль
          <input className="form-input" name="password" type="password" value={form.password} onChange={onChange} required />
        </label>
        <label className="form-label">Телефон
          <input className="form-input" name="phone" type="tel" value={form.phone} onChange={onChange} required />
        </label>
        <label className="form-label">Имя
          <input className="form-input" name="first_name" value={form.first_name} onChange={onChange} required />
        </label>
        <label className="form-label">Фамилия
          <input className="form-input" name="last_name" value={form.last_name} onChange={onChange} required />
        </label>
        <label className="form-label">Роль
          <select className="form-input" name="role" value={form.role} onChange={onChange}>
            <option value="client">Клиент</option>
            <option value="walker">Выгульщик</option>
          </select>
        </label>
        <Button disabled={loading} type="submit">Создать аккаунт</Button>
      </form>
    </main>
  );
}


