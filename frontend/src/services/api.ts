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

async function ensureSession() {
  const me = await request<MeResponse>('/api/auth/me')
  if (!me.authenticated) {
    await request('/api/auth/demo', { method: 'POST' })
  }
}

export type SavedHandRecord = {
  id: number
  title: string
  payload: Record<string, unknown>
}

const LOCAL_HANDS = 'dealt.saved-stacks'

export function readLocalHands(): SavedHandRecord[] {
  try {
    const raw = window.localStorage.getItem(LOCAL_HANDS)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    return Array.isArray(parsed) ? (parsed as SavedHandRecord[]) : []
  } catch {
    return []
  }
}

export function writeLocalHands(items: SavedHandRecord[]) {
  window.localStorage.setItem(LOCAL_HANDS, JSON.stringify(items))
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
  listHands: async () => {
    try {
      await ensureSession()
      return await request<{ items: SavedHandRecord[] }>('/api/hands')
    } catch {
      return { items: readLocalHands() }
    }
  },
  listVotes: () => request<{ items: Array<{ spotify_id: string; vote: number }> }>('/api/feedback'),
  voteTrack: (body: { spotify_id: string; artist_name: string; genres: string[]; vote: number }) =>
    request('/api/feedback', { method: 'POST', body: JSON.stringify(body) }),
  saveHand: async (payload: Record<string, unknown>, title?: string) => {
    const steps = Array.isArray(payload.steps) ? (payload.steps as Array<{ name?: string }>) : []
    const fallbackTitle =
      (title || "").trim() || `${steps[0]?.name || "Opening"} → ${steps[steps.length - 1]?.name || "Close"}`
    try {
      await ensureSession()
      const saved = await request<SavedHandRecord>("/api/hands", {
        method: "POST",
        body: JSON.stringify({ title: title || null, payload }),
      })
      const existing = readLocalHands().filter((item) => item.id !== saved.id)
      writeLocalHands([saved, ...existing])
      return saved
    } catch {
      const local: SavedHandRecord = {
        id: Date.now(),
        title: fallbackTitle,
        payload,
      }
      writeLocalHands([local, ...readLocalHands()])
      return local
    }
  },
  deleteHand: async (id: number) => {
    writeLocalHands(readLocalHands().filter((item) => item.id !== id))
    try {
      await ensureSession()
      return await request(`/api/hands/${id}`, { method: 'DELETE' })
    } catch {
      return { ok: true }
    }
  },
}
