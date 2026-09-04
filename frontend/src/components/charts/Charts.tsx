import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const tooltipStyle = {
  background: '#fcfaff',
  border: '1px solid #e4dcee',
  borderRadius: 16,
  fontSize: 13,
}

export function EvolutionChart({ data }: { data: { period: string; plays: number; unique_artists: number }[] }) {
  if (!data?.length) return null
  return (
    <div className="h-[280px] md:h-[340px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="playsFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#9d86c4" stopOpacity={0.32} />
              <stop offset="100%" stopColor="#9d86c4" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#ebe4f4" vertical={false} />
          <XAxis dataKey="period" tick={{ fill: '#7e7690', fontSize: 11 }} axisLine={false} tickLine={false} interval={2} />
          <YAxis tick={{ fill: '#7e7690', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Area type="monotone" dataKey="plays" stroke="#9d86c4" fill="url(#playsFill)" strokeWidth={2} name="Plays" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function HourChart({ data }: { data: { hour: number; label: string; event_count: number }[] }) {
  return (
    <div className="h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
          <CartesianGrid stroke="#ebe4f4" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: '#7e7690', fontSize: 10 }} interval={3} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#7e7690', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="event_count" fill="#9d86c4" radius={[8, 8, 8, 8]} name="Plays" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function WeekdayChart({ data }: { data: { label: string; event_count: number }[] }) {
  return (
    <div className="h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
          <CartesianGrid stroke="#ebe4f4" vertical={false} />
          <XAxis dataKey="label" tickFormatter={(v) => String(v).slice(0, 3)} tick={{ fill: '#7e7690', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#7e7690', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="event_count" fill="#8aa3d4" radius={[8, 8, 8, 8]} name="Plays" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
