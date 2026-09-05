import { useId } from "react"

function starPath(cx: number, cy: number, outer: number, inner: number, points = 5) {
  const coords: string[] = []
  for (let i = 0; i < points * 2; i += 1) {
    const radius = i % 2 === 0 ? outer : inner
    const angle = -Math.PI / 2 + (i * Math.PI) / points
    coords.push(`${cx + radius * Math.cos(angle)},${cy + radius * Math.sin(angle)}`)
  }
  return coords.join(" ")
}

function OutlineStar({ size, sparse = false }: { size: number; sparse?: boolean }) {
  const cx = size / 2
  const cy = size / 2
  const outer = size * 0.46
  const inner = size * 0.18
  const dots: Array<[number, number]> = []
  const points = 5 * 2
  const corners: Array<[number, number]> = []
  for (let i = 0; i < points; i += 1) {
    const radius = i % 2 === 0 ? outer : inner
    const angle = -Math.PI / 2 + (i * Math.PI) / 5
    corners.push([cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)])
  }
  const step = sparse ? 7 : 5
  for (let i = 0; i < corners.length; i += 1) {
    const [x1, y1] = corners[i]
    const [x2, y2] = corners[(i + 1) % corners.length]
    const dist = Math.hypot(x2 - x1, y2 - y1)
    const count = Math.max(3, Math.round(dist / step))
    for (let t = 0; t < count; t += 1) {
      const p = t / count
      dots.push([x1 + (x2 - x1) * p, y1 + (y2 - y1) * p])
    }
  }
  if (sparse) {
    dots.push([cx, cy], [cx, cy - outer * 0.35], [cx, cy + outer * 0.22])
  }
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
      {dots.map(([x, y], index) => (
        <circle key={`${x.toFixed(1)}-${y.toFixed(1)}-${index}`} cx={x} cy={y} r={1.35} fill="currentColor" />
      ))}
    </svg>
  )
}

function FilledStar({ size }: { size: number }) {
  const id = useId().replace(/:/g, "")
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
      <defs>
        <pattern id={`${id}-dots`} width="5" height="5" patternUnits="userSpaceOnUse">
          <circle cx="1.6" cy="1.6" r="1.15" fill="currentColor" />
        </pattern>
        <clipPath id={id}>
          <polygon points={starPath(size / 2, size / 2, size * 0.46, size * 0.18)} />
        </clipPath>
      </defs>
      <rect width={size} height={size} fill={`url(#${id}-dots)`} clipPath={`url(#${id})`} />
    </svg>
  )
}

function Sparkle({ size }: { size: number }) {
  const cx = size / 2
  const cy = size / 2
  const dots: Array<[number, number]> = [[cx, cy]]
  ;[0, 90, 180, 270].forEach((deg) => {
    const rad = (deg * Math.PI) / 180
    dots.push([cx + Math.cos(rad) * size * 0.32, cy + Math.sin(rad) * size * 0.32])
  })
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
      {dots.map(([x, y], index) => (
        <circle key={index} cx={x} cy={y} r={index === 0 ? 1.6 : 1.2} fill="currentColor" />
      ))}
    </svg>
  )
}

export function DottedStars() {
  return (
    <>
      <div className="ornament-col is-left hidden md:flex flex-col items-center gap-10">
        <OutlineStar size={56} sparse />
        <FilledStar size={28} />
        <Sparkle size={16} />
      </div>
      <div className="ornament-col is-right hidden md:flex flex-col items-center gap-12">
        <FilledStar size={24} />
        <OutlineStar size={44} />
        <Sparkle size={14} />
      </div>
    </>
  )
}
