import type { ReactNode } from 'react'

export function Insight({ children }: { children: string }) {
  return <p className="text-[17px] md:text-[20px] leading-snug tracking-tight text-ink max-w-2xl">{children}</p>
}

export function Section({
  kicker,
  title,
  children,
  delay = 0,
}: {
  kicker?: string
  title: string
  children: ReactNode
  delay?: number
}) {
  return (
    <section className="fade-up mt-14 md:mt-20" style={{ animationDelay: `${delay}ms` }}>
      {kicker ? (
        <p className="text-[11px] tracking-[0.2em] uppercase text-muted mb-2">{kicker}</p>
      ) : null}
      <h2 className="text-2xl md:text-[32px] font-medium tracking-tight mb-6">{title}</h2>
      {children}
    </section>
  )
}

export function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="min-w-0">
      <p className="text-[11px] tracking-[0.16em] uppercase text-muted">{label}</p>
      <p className="text-3xl md:text-5xl font-medium tracking-tight mt-2 tabular-nums">{value}</p>
      {hint ? <p className="text-sm text-muted mt-2 max-w-xs">{hint}</p> : null}
    </div>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`bg-card rounded-[28px] shadow-[0_12px_40px_rgba(80,48,120,0.06)] p-6 md:p-8 ${className}`}>{children}</div>
}

export function StateMessage({ title, body }: { title: string; body: string }) {
  return (
    <Card>
      <h3 className="text-xl font-medium">{title}</h3>
      <p className="text-muted mt-2 max-w-md">{body}</p>
    </Card>
  )
}

export function LoadingBlock() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 w-48 bg-line rounded-full" />
      <div className="h-40 bg-line/70 rounded-[28px]" />
    </div>
  )
}
