export type MeResponse = {
  authenticated: boolean
  user: {
    id: number
    display_name: string
    is_demo: boolean
    image_url: string | null
  } | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) {
    const detail = data?.detail || data?.message || response.statusText
    throw new Error(typeof detail === 'string' ? detail : 'Request failed')
  }
  return data as T
}

export const api = {
  me: () => request<MeResponse>('/api/auth/me'),
  login: () => request<{ url: string }>('/api/auth/login'),
  demo: () => request('/api/auth/demo', { method: 'POST' }),
  logout: () => request('/api/auth/logout', { method: 'POST' }),
  sync: () => request('/api/data/sync', { method: 'POST' }),
  clear: () => request('/api/data/me', { method: 'DELETE' }),
  overview: () => request<Record<string, unknown>>('/api/analytics/overview'),
  evolution: () => request<Record<string, unknown>>('/api/analytics/evolution'),
  transitions: (params?: { min_count?: number; artist_id?: number }) => {
    const search = new URLSearchParams()
    if (params?.min_count) search.set('min_count', String(params.min_count))
    if (params?.artist_id) search.set('artist_id', String(params.artist_id))
    const suffix = search.toString() ? `?${search}` : ''
    return request<Record<string, unknown>>(`/api/analytics/transitions${suffix}`)
  },
  patterns: () => request<Record<string, unknown>>('/api/analytics/time-patterns'),
  taste: () => request<Record<string, unknown>>('/api/analytics/taste'),
  recommendations: () => request<{ items: unknown[]; empty: boolean; message: string | null }>(
    '/api/analytics/recommendations',
  ),
  discoverCatalog: () => request<{ items: unknown[] }>('/api/discover/catalog'),
  similarTracks: (query: string) =>
    request<Record<string, unknown>>('/api/discover/similar', {
      method: 'POST',
      body: JSON.stringify({ query }),
    }),
  bridgePlaylist: (start: string, end: string, length = 7, unit: 'songs' | 'minutes' = 'songs') =>
    request<Record<string, unknown>>('/api/discover/bridge', {
      method: 'POST',
      body: JSON.stringify({ start, end, length, unit }),
    }),
}
