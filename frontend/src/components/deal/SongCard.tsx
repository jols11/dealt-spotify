const SUITS = ["♠", "♥", "♦", "♣"]

export type DealtTrack = {
  spotify_id: string
  name: string
  artist_name: string
  album_name?: string | null
  url: string
  image_url?: string | null
  role?: string
  reason?: string
  duration_ms?: number
  genres?: string[]
}

export function formatLength(ms?: number) {
  if (!ms) return ""
  const total = Math.round(ms / 1000)
  const minutes = Math.floor(total / 60)
  const seconds = String(total % 60).padStart(2, "0")
  return `${minutes}:${seconds}`
}

export function SongCard({
  track,
  index,
  isFront,
  peekOffset,
  onAdvance,
  layout = "stack",
  playable = true,
  vote = 0,
  onVote,
}: {
  track: DealtTrack
  index: number
  isFront: boolean
  peekOffset: number
  onAdvance?: () => void
  layout?: "stack" | "fan" | "row"
  playable?: boolean
  vote?: number
  onVote?: (value: 1 | -1) => void
}) {
  const suit = SUITS[index % SUITS.length]
  const rank = String(index + 1).padStart(2, "0")
  const liveId = Boolean(track.spotify_id && !track.spotify_id.startsWith("syn-") && !track.spotify_id.startsWith("preview-"))
  const showEmbed = playable && isFront && liveId
  const length = formatLength(track.duration_ms)

  return (
    <article
      className={`song-card ${isFront ? "is-front" : "is-peek"} ${layout === "fan" ? `is-fan is-fan-${peekOffset}` : ""} ${layout === "row" ? (isFront ? "is-row-front" : "is-row-peek") : ""}`}
      style={
        layout === "fan" || layout === "row"
          ? {}
          : {
              transform: `translate(${peekOffset * 18}px, ${peekOffset * 14}px)`,
              zIndex: 40 - peekOffset,
            }
      }
      onClick={() => {
        if (!isFront) onAdvance?.()
      }}
    >
      <div className="song-rank">
        {rank}
        <span>{suit}</span>
      </div>
      {isFront ? (
        <div className="song-rank song-rank-br">
          {rank}
          <span>{suit}</span>
        </div>
      ) : null}
      <div className="song-art">
        {track.image_url ? (
          <div className="song-art-photo" style={{ backgroundImage: `url(${track.image_url})` }} />
        ) : null}
        <div className="song-art-dots" />
      </div>
      <div className="song-card-body">
        {isFront && track.role ? (
          <p className="text-[10px] tracking-[0.2em] uppercase mb-1">
            {track.role === "start" ? "Opening" : track.role === "end" ? "River" : "Turn"}
          </p>
        ) : null}
        <h3 className="song-title">{track.name}</h3>
        {isFront ? (
          <>
            <p className="mt-2 text-sm">{track.artist_name}</p>
            <p className="mt-1 text-xs opacity-80">
              {[length, track.album_name].filter(Boolean).join(" · ")}
            </p>
            {track.reason ? <p className="mt-2 text-[11px] leading-snug opacity-80">{track.reason}</p> : null}
            {onVote ? (
              <div className="vote-row" onClick={(event) => event.stopPropagation()}>
                <button type="button" className={`vote-btn ${vote === 1 ? "is-on" : ""}`} onClick={() => onVote(1)} aria-label="Thumbs up">
                  👍
                </button>
                <button type="button" className={`vote-btn ${vote === -1 ? "is-on" : ""}`} onClick={() => onVote(-1)} aria-label="Thumbs down">
                  👎
                </button>
              </div>
            ) : null}
            {showEmbed ? (
              <div className="embed-slot">
                <iframe
                  title={track.name}
                  src={`https://open.spotify.com/embed/track/${track.spotify_id}?utm_source=generator`}
                  width="100%"
                  height="152"
                  allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                  loading="lazy"
                />
              </div>
            ) : playable ? (
              <p className="mt-3 text-[11px] leading-snug opacity-70">
                Connect Spotify (and keep the API running) so this card can play. Demo catalog ids cannot stream.
              </p>
            ) : null}
          </>
        ) : (
          <p className="song-peek-artist">{track.artist_name}</p>
        )}
      </div>
    </article>
  )
}
