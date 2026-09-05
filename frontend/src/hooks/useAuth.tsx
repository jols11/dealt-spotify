import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, type MeResponse } from '../services/api'

type AuthContextValue = {
  loading: boolean
  me: MeResponse | null
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue>({
  loading: true,
  me: null,
  refresh: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [me, setMe] = useState<MeResponse | null>(null)

  async function refresh() {
    try {
      const data = await api.me()
      setMe(data)
    } catch {
      setMe({ authenticated: false, user: null, spotify_configured: false, catalog_ready: false })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  return <AuthContext.Provider value={{ loading, me, refresh }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
