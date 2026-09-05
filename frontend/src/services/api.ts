export type MeResponse = {
  authenticated: boolean
  spotify_configured: boolean
  catalog_ready: boolean
  api_unreachable?: boolean
  user: {
    id: number
    display_name: string
    is_demo: boolean
    image_url: string | null
  } | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
      ...init,
    })
  } catch {
    throw new Error('Cannot reach the API. Start uvicorn on port 8765, then refresh.')
  }
  const text = await response.text()
  let data: { detail?: string; message?: string } | null = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = null
    }
  }
  if (!response.ok) {
    if (response.status === 502 || response.status === 504) {
      throw new Error('The API on port 8765 is not running. Start uvicorn, then refresh.')
    }
    const detail = data?.detail || data?.message || response.statusText
    throw new Error(typeof detail === 'string' ? detail : 'Request failed')
  }
  return data as T
}

export const api = {
  me: () => request<MeResponse>('/api/auth/me'),
  login: () => request<{ url: string }>('/api/auth/login'),
  demo: () => request('/api/auth/demo', { method: 'POST' }),
  searchTracks: (q: string) =>
    request<{ items: Array<{ spotify_id: string; name: string; artist_name: string; image_url?: string | null }> }>(
      `/api/discover/search?q=${encodeURIComponent(q)}`,
    ),
  bridgePlaylist: (start: string, end: string, length = 7, unit: 'songs' | 'minutes' = 'songs') =>
    request<Record<string, unknown>>('/api/discover/bridge', {
      method: 'POST',
      body: JSON.stringify({ start, end, length, unit }),
    }),
  listHands: () => request<{ items: unknown[] }>('/api/hands'),
  saveHand: (payload: Record<string, unknown>, title?: string) =>
    request('/api/hands', { method: 'POST', body: JSON.stringify({ title, payload }) }),
  deleteHand: (id: number) => request(`/api/hands/${id}`, { method: 'DELETE' }),
}
