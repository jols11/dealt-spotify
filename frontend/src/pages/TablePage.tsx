import { useEffect, useState, type FormEvent } from 'react'
import { Deck } from '../components/deal/Deck'
import type { DealtTrack } from '../components/deal/SongCard'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

type HandRecord = {
  id: number
  title: string
  payload: { steps?: DealtTrack[]; method?: string; duration_label?: string }
}

export function TablePage() {
  const { loading, me, refresh } = useAuth()
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
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
    setBusy(true)
    setError(null)
    setSavedNote(null)
    try {
      const result = (await api.bridgePlaylist(start, end, length, unit)) as {
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
      setError(err instanceof Error ? err.message : 'Paste two Spotify track links.')
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
      setSavedNote('Hand saved.')
      await loadHands()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save this hand.')
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
      setError(err instanceof Error ? err.message : 'Add Spotify credentials in .env to look up live links.')
    }
  }

  const current = steps[active]

  return (
    <div className="table-page px-5 md:px-12 py-8 md:py-10">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] tracking-[0.28em] uppercase">The table</p>
          <h1 className="font-title text-5xl md:text-6xl leading-none mt-1">
            The Hand
            <span className="text-3xl ml-3 lowercase font-bold">deal</span>
          </h1>
        </div>
        <button type="button" onClick={() => void connect()} className="text-xs tracking-[0.16em] uppercase border-b border-current pb-0.5">
          {me?.user?.is_demo === false ? 'Spotify connected' : 'Connect Spotify'}
        </button>
      </header>

      <p className="mt-4 max-w-lg text-sm opacity-80">
        Paste two Spotify track links. We deal a hand that walks from the first song to the last. Click the card
        peeking out to play the next one.
      </p>

      <form onSubmit={(event) => void deal(event)} className="mt-8 grid md:grid-cols-2 gap-4 max-w-3xl">
        <label className="text-[11px] tracking-[0.18em] uppercase">
          First song
          <input className="input-blue" value={start} onChange={(event) => setStart(event.target.value)} placeholder="https://open.spotify.com/track/…" />
        </label>
        <label className="text-[11px] tracking-[0.18em] uppercase">
          Last song
          <input className="input-blue" value={end} onChange={(event) => setEnd(event.target.value)} placeholder="https://open.spotify.com/track/…" />
        </label>
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
              Save this hand
            </button>
          ) : null}
        </div>
      </form>
      {error ? <p className="mt-4 text-sm">{error}</p> : null}
      {savedNote ? <p className="mt-2 text-sm">{savedNote}</p> : null}

      <div className="mt-12">
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
          <div className="deck opacity-50">
            <article className="song-card is-front flex items-center justify-center">
              <p className="font-title text-4xl px-8 text-center lowercase">waiting on a deal</p>
            </article>
          </div>
        )}
      </div>

      {hands.length ? (
        <section className="mt-16 max-w-3xl">
          <p className="text-[11px] tracking-[0.2em] uppercase">Saved hands</p>
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
