import { useState, type FormEvent } from 'react'
import { PokerCard } from '../components/discover/PokerCard'
import { api } from '../services/api'

type TrackCard = {
  spotify_id: string
  name: string
  artist_name: string
  url: string
  image_url?: string | null
  role?: string
  reason?: string
  duration_ms?: number
}

export function DiscoverPage() {
  const [similarQuery, setSimilarQuery] = useState('')
  const [similar, setSimilar] = useState<{ method: string; seed: TrackCard; items: TrackCard[] } | null>(null)
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [unit, setUnit] = useState<'songs' | 'minutes'>('songs')
  const [length, setLength] = useState(7)
  const [bridge, setBridge] = useState<{
    method: string
    steps: TrackCard[]
    duration_label: string
    song_count: number
  } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  async function runBridge(event: FormEvent) {
    event.preventDefault()
    setBusy('bridge')
    setError(null)
    try {
      const result = await api.bridgePlaylist(start, end, length, unit)
      setBridge(
        result as {
          method: string
          steps: TrackCard[]
          duration_label: string
          song_count: number
        },
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not build a bridge. Paste two Spotify track links.')
    } finally {
      setBusy(null)
    }
  }

  async function runSimilar(event: FormEvent) {
    event.preventDefault()
    setBusy('similar')
    setError(null)
    try {
      const result = await api.similarTracks(similarQuery)
      setSimilar(result as { method: string; seed: TrackCard; items: TrackCard[] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Paste a Spotify track link.')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="halftone-board -mx-5 md:-mx-10 lg:-mx-16 px-5 md:px-10 lg:px-16 py-8 md:py-12 rounded-[8px]">
      <p className="text-[11px] tracking-[0.28em] uppercase text-[#2d4aa0]">From A to B</p>
      <h2 className="font-display text-5xl md:text-7xl text-[#2d4aa0] leading-none mt-2">
        DOTTED
        <span className="font-script text-4xl md:text-5xl ml-3 lowercase text-[#2d4aa0]">deal</span>
      </h2>
      <p className="mt-4 max-w-xl text-[#2d4aa0]/80">
        Paste two Spotify track links. We deal a set that walks from the first card to the last — length in songs or
        minutes. No song database to maintain; each card is looked up from the link.
      </p>
      {error ? <p className="mt-4 text-sm text-[#7a2e4a]">{error}</p> : null}

      <form onSubmit={(event) => void runBridge(event)} className="mt-8 grid gap-4 max-w-3xl">
        <label className="text-[11px] tracking-[0.2em] uppercase text-[#2d4aa0]">
          Opening link
          <input
            value={start}
            onChange={(event) => setStart(event.target.value)}
            placeholder="https://open.spotify.com/track/…"
            className="mt-2 w-full rounded-sm border-2 border-[#2d4aa0] bg-[#f7f0de] px-4 py-3 text-sm text-[#2d4aa0] outline-none"
          />
        </label>
        <label className="text-[11px] tracking-[0.2em] uppercase text-[#2d4aa0]">
          Closing link
          <input
            value={end}
            onChange={(event) => setEnd(event.target.value)}
            placeholder="https://open.spotify.com/track/…"
            className="mt-2 w-full rounded-sm border-2 border-[#2d4aa0] bg-[#f7f0de] px-4 py-3 text-sm text-[#2d4aa0] outline-none"
          />
        </label>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex rounded-full border-2 border-[#2d4aa0] overflow-hidden">
            <button
              type="button"
              onClick={() => {
                setUnit('songs')
                setLength(7)
              }}
              className={`px-4 py-2 text-sm ${unit === 'songs' ? 'bg-[#2d4aa0] text-[#f7f0de]' : 'text-[#2d4aa0]'}`}
            >
              Songs
            </button>
            <button
              type="button"
              onClick={() => {
                setUnit('minutes')
                setLength(20)
              }}
              className={`px-4 py-2 text-sm ${unit === 'minutes' ? 'bg-[#2d4aa0] text-[#f7f0de]' : 'text-[#2d4aa0]'}`}
            >
              Minutes
            </button>
          </div>
          <label className="text-[11px] tracking-[0.2em] uppercase text-[#2d4aa0]">
            {unit === 'songs' ? 'How many cards' : 'About how long'}
            <input
              type="number"
              min={unit === 'songs' ? 3 : 8}
              max={unit === 'songs' ? 16 : 90}
              value={length}
              onChange={(event) => setLength(Number(event.target.value))}
              className="mt-2 w-28 rounded-sm border-2 border-[#2d4aa0] bg-[#f7f0de] px-3 py-2 text-[#2d4aa0]"
            />
          </label>
          <button
            disabled={busy === 'bridge'}
            className="rounded-sm bg-[#2d4aa0] text-[#f7f0de] px-6 py-3 text-sm tracking-[0.14em] uppercase"
          >
            {busy === 'bridge' ? 'Dealing…' : 'Deal the set'}
          </button>
        </div>
      </form>

      {bridge ? (
        <div className="mt-12">
          <p className="text-sm text-[#2d4aa0]/80 max-w-2xl">
            {bridge.song_count} cards · {bridge.duration_label}. {bridge.method}
          </p>
          <div className="poker-hand mt-8">
            {bridge.steps.map((step, index) => (
              <PokerCard key={`${step.spotify_id}-${index}`} track={step} index={index} total={bridge.steps.length} />
            ))}
          </div>
        </div>
      ) : (
        <div className="poker-hand mt-12 opacity-70">
          {['A', 'to', 'B'].map((label, index) => (
            <div key={label} className="poker-card poker-card-blank" style={{ transform: `rotate(${(index - 1) * 6}deg)` }}>
              <span className="poker-title">{label}</span>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={(event) => void runSimilar(event)} className="mt-16 pt-10 border-t-2 border-[#2d4aa0]/30 max-w-3xl">
        <p className="font-script text-3xl text-[#2d4aa0]">neighbors</p>
        <p className="text-sm text-[#2d4aa0]/80 mt-1">Paste one track link to fan out similar cards.</p>
        <div className="mt-4 flex flex-col md:flex-row gap-3">
          <input
            value={similarQuery}
            onChange={(event) => setSimilarQuery(event.target.value)}
            placeholder="https://open.spotify.com/track/…"
            className="flex-1 rounded-sm border-2 border-[#2d4aa0] bg-[#f7f0de] px-4 py-3 text-sm text-[#2d4aa0] outline-none"
          />
          <button disabled={busy === 'similar'} className="rounded-sm border-2 border-[#2d4aa0] px-5 py-3 text-sm text-[#2d4aa0]">
            {busy === 'similar' ? 'Searching…' : 'Find neighbors'}
          </button>
        </div>
      </form>
      {similar ? (
        <div className="mt-8">
          <p className="text-sm text-[#2d4aa0]/80">{similar.method}</p>
          <div className="poker-hand mt-6">
            {similar.items.map((item, index) => (
              <PokerCard key={item.spotify_id} track={item} index={index} total={similar.items.length} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
