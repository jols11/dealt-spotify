import { SongCard, type DealtTrack } from './SongCard'

export function Deck({
  steps,
  active,
  onAdvance,
}: {
  steps: DealtTrack[]
  active: number
  onAdvance: () => void
}) {
  const remaining = steps.slice(active)
  const visible = remaining.slice(0, 4)

  return (
    <div className="deck">
      {visible
        .map((track, offset) => (
          <SongCard
            key={`${track.spotify_id}-${active + offset}`}
            track={track}
            index={active + offset}
            isFront={offset === 0}
            peekOffset={offset}
            onAdvance={onAdvance}
          />
        ))
        .reverse()}
    </div>
  )
}
