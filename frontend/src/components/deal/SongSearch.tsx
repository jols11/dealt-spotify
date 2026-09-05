import { useEffect, useRef, useState } from 'react'
import { api } from '../../services/api'

export type PickedTrack = {
  spotify_id: string
  name: string
  artist_name: string
  image_url?: string | null
}

function trackIdFromQuery(value: string) {
  const open = value.match(/open\.spotify\.com\/track\/([A-Za-z0-9]+)/)
  if (open) return open[1]
  const uri = value.match(/spotify:track:([A-Za-z0-9]+)/)
  return uri?.[1] ?? null
}

export function SongSearch({
  label,
  picked,
  onPick,
}: {
  label: string
  picked: PickedTrack | null
  onPick: (track: PickedTrack | null) => void
}) {
  const [query, setQuery] = useState('')
  const [items, setItems] = useState<PickedTrack[]>([])
  const [open, setOpen] = useState(false)
  const [searching, setSearching] = useState(false)
  const box = useRef<HTMLLabelElement>(null)

  useEffect(() => {
    function close(event: MouseEvent) {
      if (!box.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  useEffect(() => {
    const id = trackIdFromQuery(query)
    if (id) {
      onPick({
        spotify_id: id,
        name: 'Spotify track',
        artist_name: 'From link',
      })
      setOpen(false)
      return
    }
    if (query.trim().length < 2) {
      setItems([])
      return
    }
    const timer = window.setTimeout(() => {
      setSearching(true)
      void api
        .searchTracks(query.trim())
        .then((data) => {
          setItems(data.items)
          setOpen(true)
        })
        .catch(() => setItems([]))
        .finally(() => setSearching(false))
    }, 220)
    return () => window.clearTimeout(timer)
  }, [query, onPick])

  if (picked) {
    return (
      <label className="text-[11px] tracking-[0.18em] uppercase block">
        {label}
        <div className="picked-song">
          <span className="normal-case tracking-normal text-sm">
            {picked.name}
            <span className="opacity-70"> — {picked.artist_name}</span>
          </span>
          <button type="button" className="text-[11px] uppercase tracking-[0.12em]" onClick={() => onPick(null)}>
            Clear
          </button>
        </div>
      </label>
    )
  }

  return (
    <label ref={box} className="text-[11px] tracking-[0.18em] uppercase block relative">
      {label}
      <input
        className="input-blue"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onFocus={() => items.length && setOpen(true)}
        placeholder="Song or artist — or a Spotify link"
        autoComplete="off"
      />
      {open && items.length ? (
        <div className="search-results">
          {items.map((item) => (
            <button
              key={item.spotify_id}
              type="button"
              className="search-result"
              onClick={() => {
                onPick(item)
                setQuery('')
                setOpen(false)
              }}
            >
              <span className="normal-case tracking-normal text-sm">
                {item.name}
                <span className="block text-[11px] opacity-80">{item.artist_name}</span>
              </span>
            </button>
          ))}
        </div>
      ) : null}
      {searching ? <p className="mt-1 normal-case tracking-normal text-[11px] opacity-70">Searching Spotify…</p> : null}
    </label>
  )
}
