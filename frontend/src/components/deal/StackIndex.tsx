import { formatLength, type DealtTrack } from './SongCard'

function roleLabel(role?: string) {
  if (role === 'start') return 'Opening'
  if (role === 'end') return 'River'
  if (role) return 'Turn'
  return ''
}

export function StackIndex({
  steps,
  active,
  onSelect,
}: {
  steps: DealtTrack[]
  active: number
  onSelect: (index: number) => void
}) {
  return (
    <nav className="stack-toc" aria-label="Songs in this stack">
      <p className="stack-toc-kicker">The stack</p>
      <ol className="stack-toc-list">
        {steps.map((track, index) => {
          const length = formatLength(track.duration_ms)
          const role = roleLabel(track.role)
          const genres = (track.genres || []).slice(0, 2).join(' · ')
          const meta = [length, genres].filter(Boolean).join(' · ')
          return (
            <li key={`${track.spotify_id}-${index}`}>
              <button
                type="button"
                className={`stack-toc-item ${index === active ? 'is-on' : ''}`}
                onClick={() => onSelect(index)}
              >
                <span className="stack-toc-num">{String(index + 1).padStart(2, '0')}</span>
                <span className="stack-toc-copy">
                  {role ? <span className="stack-toc-role">{role}</span> : null}
                  <span className="stack-toc-title">{track.name}</span>
                  <span className="stack-toc-artist">{track.artist_name}</span>
                  {meta ? <span className="stack-toc-meta">{meta}</span> : null}
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
