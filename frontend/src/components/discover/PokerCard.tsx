const SUITS = ["♠", "♥", "♦", "♣"]

type PokerTrack = {
  spotify_id: string
  name: string
  artist_name: string
  url: string
  image_url?: string | null
  role?: string
  reason?: string
  duration_ms?: number
}

export function PokerCard({
  track,
  index,
  total,
}: {
  track: PokerTrack
  index: number
  total: number
}) {
  const suit = SUITS[index % SUITS.length]
  const rank = String(index + 1).padStart(2, "0")
  const mid = (total - 1) / 2
  const tilt = total <= 1 ? 0 : (index - mid) * 4.5

  return (
    <a
      href={track.url}
      target="_blank"
      rel="noreferrer"
      className="poker-card fade-up"
      style={{
        transform: `rotate(${tilt}deg)`,
        animationDelay: `${index * 70}ms`,
      }}
    >
      <span className="poker-corner poker-corner-tl">
        {rank}
        <i>{suit}</i>
      </span>
      <span className="poker-corner poker-corner-br">
        {rank}
        <i>{suit}</i>
      </span>
      <span className="poker-role">{track.role === "start" ? "open" : track.role === "end" ? "close" : "through"}</span>
      <h3 className="poker-title">{track.name}</h3>
      <p className="poker-artist">{track.artist_name}</p>
      {track.reason ? <p className="poker-why">{track.reason}</p> : null}
      <span className="poker-pip">{suit}</span>
    </a>
  )
}
