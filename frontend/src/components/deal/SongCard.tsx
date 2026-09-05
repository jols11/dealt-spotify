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
}

function formatLength(ms?: number) {
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
}: {
  track: DealtTrack
  index: number
  isFront: boolean
  peekOffset: number
  onAdvance?: () => void
  layout?: "stack" | "fan"
  playable?: boolean
}) {
  const suit = SUITS[index % SUITS.length]
  const rank = String(index + 1).padStart(2, "0")
  const showEmbed = playable && isFront && track.spotify_id && !track.spotify_id.startsWith("syn-")
  const length = formatLength(track.duration_ms)

  return (
    <article
      className={`song-card ${isFront ? "is-front" : "is-peek"} ${layout === "fan" ? `is-fan is-fan-${peekOffset}` : ""}`}
      style={
        layout === "fan"
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
      <div className="song-rank song-rank-br">
        {rank}
        <span>{suit}</span>
      </div>
      <div className="song-art">
        {track.image_url ? (
          <div className="song-art-photo" style={{ backgroundImage: `url(${track.image_url})` }} />
        ) : null}
        <div className="song-art-dots" />
      </div>
      <div className="song-card-body">
        {track.role ? (
          <p className="text-[10px] tracking-[0.2em] uppercase mb-1">
            {track.role === "start" ? "Opening" : track.role === "end" ? "River" : "Turn"}
          </p>
        ) : null}
        <h3 className="song-title">{track.name}</h3>
        <p className="mt-2 text-sm">{track.artist_name}</p>
        <p className="mt-1 text-xs opacity-80">
          {[length, track.album_name].filter(Boolean).join(" · ")}
        </p>
        {isFront && track.reason ? <p className="mt-2 text-[11px] leading-snug opacity-80">{track.reason}</p> : null}
        {showEmbed ? (
          <div className="embed-slot">
            <iframe
              title={track.name}
              src={`https://open.spotify.com/embed/track/${track.spotify_id}?utm_source=generator&theme=0`}
              width="100%"
              height="80"
              allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
              loading="lazy"
            />
          </div>
        ) : null}
      </div>
    </article>
  )
}
