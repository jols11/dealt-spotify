import { SongCard, type DealtTrack } from './SongCard'

export function Deck({
  steps,
  active,
  onSelect,
  votes,
  onVote,
}: {
  steps: DealtTrack[]
  active: number
  onSelect: (index: number) => void
  votes: Record<string, number>
  onVote: (track: DealtTrack, value: 1 | -1) => void
}) {
  return (
    <div className="row-deck">
      {steps.map((track, index) => (
        <SongCard
          key={`${track.spotify_id}-${index}`}
          track={track}
          index={index}
          isFront={index === active}
          peekOffset={index}
          layout="row"
          playable
          vote={votes[track.spotify_id] || 0}
          onVote={(value) => onVote(track, value)}
          onAdvance={() => onSelect(index)}
        />
      ))}
    </div>
  )
}
