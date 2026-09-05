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

function sampleLine(x1: number, y1: number, x2: number, y2: number, step: number) {
  const dist = Math.hypot(x2 - x1, y2 - y1)
  const count = Math.max(2, Math.round(dist / step))
  const dots: Array<[number, number]> = []
  for (let t = 0; t <= count; t += 1) {
    const p = t / count
    dots.push([x1 + (x2 - x1) * p, y1 + (y2 - y1) * p])
  }
  return dots
}

function sampleEllipse(cx: number, cy: number, rx: number, ry: number, rotation: number, step: number) {
  const circ = 2 * Math.PI * Math.sqrt((rx * rx + ry * ry) / 2)
  const count = Math.max(8, Math.round(circ / step))
  const dots: Array<[number, number]> = []
  for (let i = 0; i < count; i += 1) {
    const a = (i / count) * Math.PI * 2
    const x = rx * Math.cos(a)
    const y = ry * Math.sin(a)
    const c = Math.cos(rotation)
    const s = Math.sin(rotation)
    dots.push([cx + x * c - y * s, cy + x * s + y * c])
  }
  return dots
}

function sampleCubic(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  x3: number,
  y3: number,
  step: number,
) {
  const approx = Math.hypot(x3 - x0, y3 - y0) + Math.hypot(x1 - x0, y1 - y0) + Math.hypot(x2 - x3, y2 - y3)
  const count = Math.max(6, Math.round(approx / step))
  const dots: Array<[number, number]> = []
  for (let i = 0; i <= count; i += 1) {
    const t = i / count
    const u = 1 - t
    const x = u * u * u * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3
    const y = u * u * u * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3
    dots.push([x, y])
  }
  return dots
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
    dots.push(...sampleLine(x1, y1, x2, y2, step))
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

function OutlineNote({ size }: { size: number }) {
  const w = size
  const h = size * 1.45
  const sx = w / 40
  const sy = h / 58
  const step = 4.2
  const head = sampleEllipse(14 * sx, 46 * sy, 9 * sx, 6.2 * sy, -0.45, step)
  const stemX = 22.5 * sx
  const stem = sampleLine(stemX, 44 * sy, stemX, 8 * sy, step)
  const flag = sampleCubic(stemX, 8 * sy, 32 * sx, 10 * sy, 38 * sx, 20 * sy, 30 * sx, 28 * sy, step)
  const dots = [...head, ...stem, ...flag]
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
      {dots.map(([x, y], index) => (
        <circle key={`${x.toFixed(1)}-${index}`} cx={x} cy={y} r={1.3} fill="currentColor" />
      ))}
    </svg>
  )
}

function FilledNote({ size }: { size: number }) {
  const id = useId().replace(/:/g, "")
  const w = size
  const h = size * 1.45
  return (
    <svg width={w} height={h} viewBox="0 0 40 58" aria-hidden="true">
      <defs>
        <pattern id={`${id}-dots`} width="5" height="5" patternUnits="userSpaceOnUse">
          <circle cx="1.55" cy="1.55" r="1.12" fill="currentColor" />
        </pattern>
        <clipPath id={id}>
          <ellipse cx="14" cy="46" rx="9.4" ry="6.4" transform="rotate(-26 14 46)" />
          <rect x="21.2" y="8" width="2.6" height="37" />
          <path d="M23.6 8 C34 9 40 18 36 27 C31 18 26 11 23.6 10 Z" />
        </clipPath>
      </defs>
      <rect width="40" height="58" fill={`url(#${id}-dots)`} clipPath={`url(#${id})`} />
    </svg>
  )
}

function BeamedNotes({ size }: { size: number }) {
  const w = size * 1.7
  const h = size * 1.2
  const sx = w / 70
  const sy = h / 48
  const step = 4.4
  const dots = [
    ...sampleEllipse(14 * sx, 38 * sy, 7.5 * sx, 5.2 * sy, -0.4, step),
    ...sampleEllipse(44 * sx, 40 * sy, 7.5 * sx, 5.2 * sy, -0.4, step),
    ...sampleLine(20.5 * sx, 36 * sy, 20.5 * sx, 10 * sy, step),
    ...sampleLine(50.5 * sx, 38 * sy, 50.5 * sx, 12 * sy, step),
    ...sampleLine(20.5 * sx, 10 * sy, 50.5 * sx, 12 * sy, step),
    ...sampleLine(20.5 * sx, 14 * sy, 50.5 * sx, 16 * sy, step),
  ]
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
      {dots.map(([x, y], index) => (
        <circle key={`${x.toFixed(1)}-${index}`} cx={x} cy={y} r={1.25} fill="currentColor" />
      ))}
    </svg>
  )
}

export function DottedStars({ hideRight = false }: { hideRight?: boolean }) {
  return (
    <>
      <div className="ornament-col is-left hidden md:flex flex-col items-center gap-10">
        <OutlineNote size={42} />
        <OutlineStar size={48} sparse />
        <FilledNote size={26} />
        <Sparkle size={16} />
        <BeamedNotes size={28} />
      </div>
      {hideRight ? null : (
        <div className="ornament-col is-right hidden md:flex flex-col items-center gap-12">
          <FilledStar size={24} />
          <OutlineNote size={36} />
          <OutlineStar size={40} />
          <FilledNote size={22} />
          <Sparkle size={14} />
        </div>
      )}
    </>
  )
}
