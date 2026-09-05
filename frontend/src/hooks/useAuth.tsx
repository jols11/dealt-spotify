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

async function wait(ms: number) {
  await new Promise((resolve) => window.setTimeout(resolve, ms))
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [me, setMe] = useState<MeResponse | null>(null)

  async function refresh() {
    for (let attempt = 0; attempt < 10; attempt += 1) {
      try {
        const data = await api.me()
        setMe(data)
        return
      } catch {
        await wait(400)
      }
    }
    setMe({
      authenticated: false,
      user: null,
      spotify_configured: false,
      catalog_ready: false,
      api_unreachable: true,
    })
  }

  useEffect(() => {
    void refresh().finally(() => setLoading(false))
  }, [])

  return <AuthContext.Provider value={{ loading, me, refresh }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
