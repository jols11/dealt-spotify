import { useEffect, useState, type FormEvent } from 'react'
import { Card, Insight, Section } from '../components/ui/primitives'
import { api } from '../services/api'

type TrackCard = {
  spotify_id: string
  name: string
  artist_name: string
  genres: string[]
  url: string
  source: string
  reason?: string
  role?: string
}

export function DiscoverPage() {
  const [catalog, setCatalog] = useState<TrackCard[]>([])
  const [similarQuery, setSimilarQuery] = useState('SZA Kill Bill')
  const [similar, setSimilar] = useState<{ method: string; seed: TrackCard; items: TrackCard[] } | null>(null)
  const [start, setStart] = useState('Drake Passionfruit')
  const [end, setEnd] = useState('Phoebe Bridgers Kyoto')
  const [bridge, setBridge] = useState<{ method: string; steps: TrackCard[] } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  useEffect(() => {
    void api.discoverCatalog().then((data) => setCatalog(data.items as TrackCard[])).catch(() => undefined)
  }, [])

  async function runSimilar(event: FormEvent) {
    event.preventDefault()
    setBusy('similar')
    setError(null)
    try {
      const result = await api.similarTracks(similarQuery)
      setSimilar(result as { method: string; seed: TrackCard; items: TrackCard[] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not find similar tracks.')
    } finally {
      setBusy(null)
    }
  }

  async function runBridge(event: FormEvent) {
    event.preventDefault()
    setBusy('bridge')
    setError(null)
    try {
      const result = await api.bridgePlaylist(start, end, 7)
      setBridge(result as { method: string; steps: TrackCard[] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not build a bridge.')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div>
      <p className="text-[11px] tracking-[0.2em] uppercase text-muted">Personalized listening tools</p>
      <h2 className="text-4xl md:text-5xl font-medium tracking-tight mt-3">Discover</h2>
      <div className="mt-6">
        <Insight>
          Connect Spotify in Settings to use your own recently played history. These two tools never call Spotify Radio
          or audio-features — they use links, genre tags, search, and your session graph.
        </Insight>
      </div>
      {error ? <p className="text-sm text-accent mt-6">{error}</p> : null}

      <Section kicker="From A to B" title="A set that walks from one song to another">
        <Card>
          <p className="text-muted text-sm max-w-2xl">
            Pick an opening track and a destination. The path is a shortest walk across shared genres and the artist
            handoffs in this library — a flow of artists, not a claim about BPM or mood.
          </p>
          <form onSubmit={(event) => void runBridge(event)} className="mt-6 grid md:grid-cols-2 gap-4">
            <label className="text-sm">
              First song
              <input
                value={start}
                onChange={(event) => setStart(event.target.value)}
                placeholder="Spotify link or “Artist Title”"
                className="mt-2 w-full rounded-full border border-line bg-paper px-4 py-3 text-sm outline-none focus:border-accent"
              />
            </label>
            <label className="text-sm">
              Last song
              <input
                value={end}
                onChange={(event) => setEnd(event.target.value)}
                placeholder="Spotify link or “Artist Title”"
                className="mt-2 w-full rounded-full border border-line bg-paper px-4 py-3 text-sm outline-none focus:border-accent"
              />
            </label>
            <div className="md:col-span-2">
              <button disabled={busy === 'bridge'} className="rounded-full bg-ink text-paper px-5 py-3 text-sm">
                {busy === 'bridge' ? 'Building…' : 'Build the bridge'}
              </button>
            </div>
          </form>
          {bridge ? (
            <ol className="mt-8 space-y-4">
              <p className="text-sm text-muted">{bridge.method}</p>
              {bridge.steps.map((step, index) => (
                <li key={`${step.spotify_id}-${index}`} className="border-b border-line pb-4">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-muted">
                    {String(index + 1).padStart(2, '0')} · {step.role}
                  </p>
                  <p className="text-xl mt-1">
                    {step.name} <span className="text-muted">— {step.artist_name}</span>
                  </p>
                  <p className="text-sm text-muted mt-1">{step.reason}</p>
                </li>
              ))}
            </ol>
          ) : null}
        </Card>
      </Section>

      <Section kicker="Neighbors" title="Songs in the same neighborhood">
        <Card>
          <p className="text-muted text-sm max-w-2xl">
            Paste an open.spotify.com/track link. We look up the track, then suggest others by the same artist, shared
            genre tags, and artists you already move between in sessions.
          </p>
          <form onSubmit={(event) => void runSimilar(event)} className="mt-6 flex flex-col md:flex-row gap-3">
            <input
              value={similarQuery}
              onChange={(event) => setSimilarQuery(event.target.value)}
              placeholder="https://open.spotify.com/track/…"
              className="flex-1 rounded-full border border-line bg-paper px-4 py-3 text-sm outline-none focus:border-accent"
            />
            <button disabled={busy === 'similar'} className="rounded-full bg-ink text-paper px-5 py-3 text-sm">
              {busy === 'similar' ? 'Searching…' : 'Find neighbors'}
            </button>
          </form>
          {similar ? (
            <div className="mt-8">
              <p className="text-sm text-muted">{similar.method}</p>
              <p className="mt-3 text-lg">
                Seed: {similar.seed.name} — {similar.seed.artist_name}
              </p>
              <div className="mt-4 space-y-4">
                {similar.items.map((item) => (
                  <div key={item.spotify_id} className="border-b border-line pb-3">
                    <p className="text-lg">
                      {item.name} <span className="text-muted">— {item.artist_name}</span>
                    </p>
                    <p className="text-sm text-muted mt-1">{item.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </Card>
      </Section>

      <Section title="Demo catalog you can type instead of a link">
        <div className="flex flex-wrap gap-2">
          {catalog.slice(0, 18).map((track) => (
            <button
              key={track.spotify_id}
              type="button"
              onClick={() => setSimilarQuery(`${track.artist_name} ${track.name}`)}
              className="rounded-full border border-line bg-card px-3 py-1.5 text-xs hover:border-accent"
            >
              {track.artist_name} · {track.name}
            </button>
          ))}
        </div>
      </Section>
    </div>
  )
}
