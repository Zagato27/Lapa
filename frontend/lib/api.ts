export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

function getApiBase() {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envBase && typeof envBase === 'string') return envBase.replace(/\/$/, '');
  if (typeof window !== 'undefined') {
    const { hostname } = window.location;
    // Локально обращаемся к API Gateway на 8080 того же хоста
    return `http://${hostname}:8080`;
  }
  return '';
}

type FetchOptions = {
  method?: HttpMethod;
  headers?: Record<string, string>;
  body?: any;
  auth?: boolean;
};

function getTokens() {
  if (typeof window === 'undefined') return { access: null as string | null, refresh: null as string | null };
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

function setTokens(access: string, refresh?: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}

export async function apiFetch<T = any>(path: string, opts: FetchOptions = {}): Promise<T> {
  const base = getApiBase();
  const url = path.startsWith('http') ? path : `${base}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers || {}),
  };

  if (opts.auth) {
    const { access } = getTokens();
    if (access) headers['Authorization'] = `Bearer ${access}`;
  }

  const doFetch = async () => fetch(url, {
    method: opts.method || 'GET',
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });

  let res = await doFetch();
  if (res.status === 401 && opts.auth) {
    // try refresh
    const { refresh } = getTokens();
    if (refresh) {
      const r = await fetch(`${base}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (r.ok) {
        const data = await r.json();
        if (data?.access_token) setTokens(data.access_token, data.refresh_token);
        // retry
        const { access } = getTokens();
        if (access) headers['Authorization'] = `Bearer ${access}`;
        res = await doFetch();
      }
    }
  }

  if (!res.ok) {
    const message = await safeJson(res);
    throw new Error(message?.detail || message?.message || `HTTP ${res.status}`);
  }

  return (await safeJson(res)) as T;
}

async function safeJson(res: Response) {
  const text = await res.text();
  try { return JSON.parse(text); } catch { return { raw: text }; }
}

export type AuthTokens = { access_token: string; refresh_token: string; token_type?: string };
export type LoginResponse = { user: any; tokens: AuthTokens };

export const AuthAPI = {
  async login(email: string, password: string) {
    return apiFetch<LoginResponse>('/api/v1/auth/login', { method: 'POST', body: { email, password } });
  },
  async register(payload: { email: string; password: string; phone: string; first_name: string; last_name: string; role?: string; }) {
    return apiFetch('/api/v1/auth/register', { method: 'POST', body: payload });
  },
  async logout() {
    return apiFetch('/api/v1/auth/logout', { method: 'POST', auth: true });
  },
  async profile() {
    return apiFetch('/api/v1/users/profile', { method: 'GET', auth: true });
  },
  async updateProfile(payload: Partial<{ first_name: string; last_name: string; phone: string; avatar_url: string; bio: string; hourly_rate: number }>) {
    return apiFetch('/api/v1/users/profile', { method: 'PUT', auth: true, body: payload });
  }
};

// Orders API (MVP)
export type Order = { id: string; status: string; walker_id?: string; address?: string; scheduled_at?: string; total_price?: number };
export const OrdersAPI = {
  async list(params?: Record<string, any>) {
    return apiFetch<{ items: Order[]; total: number }>(`/api/v1/order/orders`, { method: 'GET', auth: true, headers: params ? { 'X-Query': JSON.stringify(params) } : undefined });
  },
  async get(orderId: string) {
    return apiFetch<Order>(`/api/v1/order/orders/${orderId}`, { method: 'GET', auth: true });
  },
  async create(payload: any) {
    return apiFetch<Order>(`/api/v1/order/orders`, { method: 'POST', auth: true, body: payload });
  },
  async update(orderId: string, payload: any) {
    return apiFetch<Order>(`/api/v1/order/orders/${orderId}`, { method: 'PUT', auth: true, body: payload });
  },
  // Walker actions (MVP)
  async pendingForWalker() {
    return apiFetch<{ orders: Order[]; total: number }>(`/api/v1/order/orders/walker/pending`, { method: 'GET', auth: true });
  },
  async confirm(orderId: string) {
    return apiFetch<Order>(`/api/v1/order/orders/${orderId}/confirm`, { method: 'PUT', auth: true });
  },
  async startWalk(orderId: string) {
    return apiFetch<Order>(`/api/v1/order/orders/${orderId}/start-walk`, { method: 'PUT', auth: true });
  },
  async completeWalk(orderId: string) {
    return apiFetch<Order>(`/api/v1/order/orders/${orderId}/complete-walk`, { method: 'PUT', auth: true });
  }
};

// Payments/Wallet API (MVP)
export type WalletBalance = { balance: number; bonus_balance?: number; available_balance: number; currency?: string; is_frozen?: boolean };
export type PaymentItem = { id: string; status: string; amount: number; currency?: string; created_at?: string; order_id?: string };

export const WalletAPI = {
  async balance() {
    return apiFetch<WalletBalance>(`/api/v1/payment/wallets/balance`, { method: 'GET', auth: true });
  },
  async transactions(params?: Record<string, any>) {
    return apiFetch<{ items: PaymentItem[]; total: number }>(`/api/v1/payment/payments`, { method: 'GET', auth: true, headers: params ? { 'X-Query': JSON.stringify(params) } : undefined });
  }
};

// Pets API (MVP)
export type Pet = {
  id: string;
  name: string;
  breed: string;
  gender: string;
  avatar_url?: string;
  date_of_birth?: string;
  age_years?: number;
  age_months?: number;
  weight_kg?: number;
  is_neutered?: boolean;
};

export const PetsAPI = {
  async list(page = 1, limit = 20, opts?: { refresh?: boolean }) {
    const params = new URLSearchParams();
    params.set('page', String(page));
    params.set('limit', String(limit));
    if (opts?.refresh) params.set('refresh', 'true');
    return apiFetch<{ pets: Pet[]; total: number; page: number; limit: number; pages: number }>(`/api/v1/pets?${params.toString()}`, { method: 'GET', auth: true });
  },
  async get(petId: string) {
    return apiFetch<{ pet: Pet }>(`/api/v1/pets/${petId}`, { method: 'GET', auth: true });
  },
  async create(payload: Partial<Pet> & { name: string; breed: string; gender: string }) {
    return apiFetch<{ pet: Pet }>(`/api/v1/pets`, { method: 'POST', auth: true, body: payload });
  },
  async update(petId: string, payload: Partial<Pet>) {
    return apiFetch<{ pet: Pet }>(`/api/v1/pets/${petId}`, { method: 'PUT', auth: true, body: payload });
  },
  async delete(petId: string) {
    return apiFetch<{ message: string }>(`/api/v1/pets/${petId}`, { method: 'DELETE', auth: true });
  },
};

// Media API (upload avatar)
export type MediaFileResponse = { id?: string; file_url?: string; public_url?: string; thumbnail_url?: string; filename: string };
export const MediaAPI = {
  async uploadAvatar(file: File) {
    const envMedia = process.env.NEXT_PUBLIC_MEDIA_BASE_URL;
    const base = envMedia && typeof envMedia === 'string'
      ? envMedia.replace(/\/$/, '')
      : (typeof window !== 'undefined' ? `http://${window.location.hostname}:8007` : '');
    const url = `${base}/api/v1/files/upload`;
    const form = new FormData();
    form.append('file', file);
    form.append('title', 'avatar');
    const { access } = getTokens();
    const res = await fetch(url, {
      method: 'POST',
      headers: access ? { 'Authorization': `Bearer ${access}` } as any : undefined,
      body: form,
    });
    if (!res.ok) throw new Error('Ошибка загрузки файла');
    return (await res.json()) as MediaFileResponse;
  }
};


