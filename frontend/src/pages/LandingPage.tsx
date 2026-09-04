import { useState } from 'react'
import { api } from '../services/api'
import { useAuth } from '../hooks/useAuth'

export function LandingPage() {
  const { refresh } = useAuth()
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function openDemo() {
    setBusy('demo')
    setError(null)
    try {
      await api.demo()
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start demo mode.')
    } finally {
      setBusy(null)
    }
  }

  async function connectSpotify() {
    setBusy('spotify')
    setError(null)
    try {
      const { url } = await api.login()
      window.location.href = url
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Spotify is not configured. Add credentials in .env, or use the synthetic demo.',
      )
      setBusy(null)
    }
  }

  return (
    <div className="min-h-screen bg-paper text-ink px-6 md:px-16 py-10 md:py-16">
      <p className="text-[11px] tracking-[0.22em] uppercase text-muted">A behavioral listening study</p>
      <div className="grid lg:grid-cols-[1.2fr_0.8fr] gap-12 mt-8 items-end">
        <div>
          <h1 className="text-5xl md:text-7xl font-medium tracking-tight leading-[0.95] max-w-3xl">
            How does your listening evolve?
          </h1>
          <p className="mt-8 text-lg md:text-xl text-[#3c3834] max-w-xl leading-relaxed">
            Not another year-in-review. This is a graph of the artists you move between, the hours you return to music,
            and how concentrated — or wide — your taste actually is.
          </p>
        </div>
        <div className="bg-card rounded-[32px] p-8 shadow-[0_16px_50px_rgba(40,24,16,0.06)]">
          <p className="text-sm text-muted">Start with a labeled synthetic library, or connect Spotify with the minimum scopes.</p>
          <div className="mt-6 flex flex-col gap-3">
            <button
              onClick={() => void openDemo()}
              disabled={!!busy}
              className="rounded-full bg-ink text-paper py-3.5 px-5 text-sm font-medium hover:opacity-90 disabled:opacity-50"
            >
              {busy === 'demo' ? 'Preparing demo…' : 'Explore the demo'}
            </button>
            <button
              onClick={() => void connectSpotify()}
              disabled={!!busy}
              className="rounded-full border border-line py-3.5 px-5 text-sm hover:bg-paper disabled:opacity-50"
            >
              {busy === 'spotify' ? 'Redirecting…' : 'Connect Spotify'}
            </button>
          </div>
          {error ? <p className="text-sm text-accent mt-4">{error}</p> : null}
          <p className="text-[12px] text-muted mt-6 leading-relaxed">
            Spotify recently-played history is a short window. The demo exists so the product can be reviewed without
            credentials, and so the graph has enough sessions to mean something.
          </p>
        </div>
      </div>
    </div>
  )
}
