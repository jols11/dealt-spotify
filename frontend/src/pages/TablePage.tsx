import { useEffect, useState, type FormEvent } from 'react'
import { Deck } from '../components/deal/Deck'
import type { DealtTrack } from '../components/deal/SongCard'
import { SongSearch, dealRef, type PickedTrack } from '../components/deal/SongSearch'
import { TableFan } from '../components/deal/TableFan'
import { DottedStars } from '../components/ornament/DottedStars'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

type HandRecord = {
  id: number
  title: string
  payload: { steps?: DealtTrack[]; method?: string; duration_label?: string }
}

export function TablePage() {
  const { loading, me, refresh } = useAuth()
  const [start, setStart] = useState<PickedTrack | null>(null)
  const [end, setEnd] = useState<PickedTrack | null>(null)
  const [startQuery, setStartQuery] = useState('')
  const [endQuery, setEndQuery] = useState('')
  const [unit, setUnit] = useState<'songs' | 'minutes'>('songs')
  const [length, setLength] = useState(7)
  const [steps, setSteps] = useState<DealtTrack[]>([])
  const [method, setMethod] = useState('')
  const [meta, setMeta] = useState('')
  const [active, setActive] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [hands, setHands] = useState<HandRecord[]>([])
  const [savedNote, setSavedNote] = useState<string | null>(null)

  const liveSpotify = me?.user?.is_demo === false
  const catalogReady = Boolean(me?.catalog_ready)
  const apiUnreachable = Boolean(me?.api_unreachable)

  useEffect(() => {
    if (loading) return
    if (!me?.authenticated) {
      void api.demo().then(() => refresh()).catch((err: Error) => setError(err.message))
    }
  }, [loading, me?.authenticated, refresh])

  async function loadHands() {
    try {
      const data = await api.listHands()
      setHands(data.items as HandRecord[])
    } catch {
      setHands([])
    }
  }

  useEffect(() => {
    if (me?.authenticated) void loadHands()
  }, [me?.authenticated])

  async function deal(event: FormEvent) {
    event.preventDefault()
    const opening = dealRef(start, startQuery)
    const closing = dealRef(end, endQuery)
    if (!opening || !closing) {
      setError('Type an opening song and a closing song, then Deal. You can click a result from the list, or just Deal with the names you typed.')
      return
    }
    setBusy(true)
    setError(null)
    setSavedNote(null)
    try {
      const result = (await api.bridgePlaylist(opening, closing, length, unit)) as {
        steps: DealtTrack[]
        method: string
        duration_label: string
        song_count: number
      }
      setSteps(result.steps)
      setActive(0)
      setMethod(result.method)
      setMeta(`${result.song_count} cards · ${result.duration_label}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not deal those two songs.')
    } finally {
      setBusy(false)
    }
  }

  async function saveHand() {
    if (!steps.length) return
    try {
      await api.saveHand({
        steps,
        method,
        duration_label: meta,
      })
      setSavedNote('Saved this stack.')
      await loadHands()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save this stack.')
    }
  }

  function openHand(hand: HandRecord) {
    const next = hand.payload.steps || []
    setSteps(next)
    setActive(0)
    setMethod(hand.payload.method || '')
    setMeta(hand.payload.duration_label || hand.title)
  }

  async function connect() {
    try {
      const { url } = await api.login()
      window.location.href = url
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Add SPOTIFY_CLIENT_ID to .env, then click Connect Spotify.',
      )
    }
  }

  const current = steps[active]

  return (
    <div className="table-page px-5 md:px-16 py-8 md:py-10">
      <DottedStars />

      <header className="relative z-10 flex items-start justify-between gap-4">
        <p className="text-[11px] tracking-[0.28em] uppercase">Two songs, one stack</p>
        <button type="button" onClick={() => void connect()} className="text-xs tracking-[0.16em] uppercase border-b border-current pb-0.5">
          {liveSpotify ? 'Spotify connected' : 'Connect Spotify'}
        </button>
      </header>

      <h1 className="wordmark relative z-10 mt-3">Dealt</h1>

      <p className="relative z-10 mt-4 max-w-lg text-sm opacity-80">
        Search an opening track and a closing track, then Deal — you can type the names and Deal without clicking the list. We deal the cards between them.
      </p>

      <p className="relative z-10 mt-3 max-w-xl text-xs opacity-75 leading-relaxed">
        {apiUnreachable
          ? 'The API is not running. Start uvicorn on port 8765, then refresh. Spotify credentials live in the repo-root .env file that the API reads — saving them in the editor is not enough until the API is restarted.'
          : liveSpotify
            ? 'Spotify is connected. Search uses the live catalog, and the player on the front card is Spotify’s embed for that track.'
            : catalogReady
              ? 'Spotify catalog search is on. Click Connect Spotify to log in for playback on the front card.'
              : 'Search still uses the demo catalog because this API process does not see SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET. Put them in the repo-root .env (no quotes), restart the API, then Connect Spotify. Redirect URI: http://127.0.0.1:8765/api/auth/callback — for a live deploy, also set PUBLIC_BASE_URL.'}
      </p>

      <form onSubmit={(event) => void deal(event)} className="relative z-10 mt-8 grid md:grid-cols-2 gap-4 max-w-3xl">
        <SongSearch label="First song" picked={start} onPick={setStart} query={startQuery} onQuery={setStartQuery} />
        <SongSearch label="Last song" picked={end} onPick={setEnd} query={endQuery} onQuery={setEndQuery} />
        <div className="md:col-span-2 flex flex-wrap items-end gap-3">
          <div className="flex">
            <button type="button" className={`pill-blue ${unit === 'songs' ? 'is-on' : ''}`} onClick={() => { setUnit('songs'); setLength(7) }}>
              Songs
            </button>
            <button type="button" className={`pill-blue ${unit === 'minutes' ? 'is-on' : ''}`} onClick={() => { setUnit('minutes'); setLength(20) }}>
              Minutes
            </button>
          </div>
          <label className="text-[11px] tracking-[0.18em] uppercase">
            {unit === 'songs' ? 'Cards' : 'Minutes'}
            <input
              className="input-blue w-24"
              type="number"
              min={unit === 'songs' ? 3 : 8}
              max={unit === 'songs' ? 16 : 90}
              value={length}
              onChange={(event) => setLength(Number(event.target.value))}
            />
          </label>
          <button disabled={busy} className="pill-blue is-on px-6 py-3">
            {busy ? 'Dealing…' : 'Deal'}
          </button>
          {steps.length ? (
            <button type="button" onClick={() => void saveHand()} className="pill-blue py-3">
              Save this stack
            </button>
          ) : null}
        </div>
      </form>
      {error ? <p className="relative z-10 mt-4 text-sm">{error}</p> : null}
      {savedNote ? <p className="relative z-10 mt-2 text-sm">{savedNote}</p> : null}

      <div className="relative z-10 mt-12">
        {steps.length ? (
          <>
            <p className="text-center text-sm opacity-80 mb-6">
              {current ? `${current.name} — ${current.artist_name}` : ''}
              <span className="mx-2">·</span>
              {active + 1} / {steps.length}
              {meta ? ` · ${meta}` : ''}
            </p>
            <Deck
              steps={steps}
              active={active}
              onAdvance={() => setActive((value) => Math.min(value + 1, steps.length - 1))}
            />
            <div className="flex justify-center gap-4 mt-8">
              <button type="button" className="pill-blue" onClick={() => setActive((value) => Math.max(0, value - 1))} disabled={active === 0}>
                Previous
              </button>
              <button
                type="button"
                className="pill-blue is-on"
                onClick={() => setActive((value) => Math.min(value + 1, steps.length - 1))}
                disabled={active >= steps.length - 1}
              >
                Next card
              </button>
            </div>
            <p className="text-center text-xs mt-4 max-w-md mx-auto opacity-70">{method}</p>
          </>
        ) : (
          <TableFan />
        )}
      </div>

      {hands.length ? (
        <section className="relative z-10 mt-16 max-w-3xl">
          <p className="text-[11px] tracking-[0.2em] uppercase">Saved stacks</p>
          <ul className="mt-3 space-y-2">
            {hands.map((hand) => (
              <li key={hand.id} className="flex items-center justify-between gap-3 border-b border-[#2d4aa0]/30 py-2">
                <button type="button" className="text-left" onClick={() => openHand(hand)}>
                  {hand.title}
                </button>
                <button
                  type="button"
                  className="text-xs uppercase tracking-[0.12em]"
                  onClick={() => void api.deleteHand(hand.id).then(loadHands)}
                >
                  Fold
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}
