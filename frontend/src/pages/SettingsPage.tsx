import { useState } from 'react'
import { Card } from '../components/ui/primitives'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

export function SettingsPage() {
  const { me, refresh } = useAuth()
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function sync() {
    setBusy(true)
    setMessage(null)
    try {
      const result = await api.sync() as { message?: string; note?: string; inserted?: number }
      setMessage(result.message || result.note || `Synced. ${result.inserted ?? 0} new events.`)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Sync failed.')
    } finally {
      setBusy(false)
    }
  }

  async function connectSpotify() {
    setBusy(true)
    setMessage(null)
    try {
      const { url } = await api.login()
      window.location.href = url
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Add SPOTIFY_CLIENT_ID to .env to connect a real account.')
      setBusy(false)
    }
  }
  async function logout() {
    await api.logout()
    await refresh()
  }

  async function clearData() {
    if (!window.confirm('Delete this listening library from the local database?')) return
    setBusy(true)
    try {
      await api.clear()
      await refresh()
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not clear data.')
      setBusy(false)
    }
  }

  return (
    <div>
      <p className="text-[11px] tracking-[0.2em] uppercase text-muted">Data & privacy</p>
      <h2 className="text-4xl md:text-5xl font-medium tracking-tight mt-3">Settings</h2>
      <div className="grid md:grid-cols-2 gap-6 mt-10">
        <Card>
          <h3 className="text-xl font-medium">This session</h3>
          <p className="text-muted mt-2">{me?.user?.display_name}</p>
          <p className="text-sm text-muted mt-1">{me?.user?.is_demo ? 'Synthetic demo library' : 'Spotify-connected library'}</p>
          <div className="flex flex-wrap gap-3 mt-6">
            <button onClick={() => void sync()} disabled={busy} className="rounded-full bg-ink text-paper px-4 py-2 text-sm">
              Refresh data
            </button>
            {me?.user?.is_demo ? (
              <button onClick={() => void connectSpotify()} disabled={busy} className="rounded-full border border-accent text-accent px-4 py-2 text-sm">
                Connect my Spotify
              </button>
            ) : null}
            <button onClick={() => void logout()} className="rounded-full border border-line px-4 py-2 text-sm">
              Sign out
            </button>
          </div>
          {message ? <p className="text-sm mt-4">{message}</p> : null}
        </Card>
        <Card>
          <h3 className="text-xl font-medium">What we store</h3>
          <p className="text-muted mt-2 leading-relaxed">
            Tokens stay on the server, encrypted at rest with the session secret. Listening events live in a local
            SQLite file that is not committed to git. Scopes are limited to recently played, top artists/tracks, and
            profile. Audio features are not requested.
          </p>
          <button onClick={() => void clearData()} disabled={busy} className="mt-6 rounded-full border border-accent text-accent px-4 py-2 text-sm">
            Clear my data
          </button>
        </Card>
      </div>
    </div>
  )
}
