import { HourChart, WeekdayChart } from '../components/charts/Charts'
import { Card, Insight, LoadingBlock, Section, StateMessage } from '../components/ui/primitives'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'

type Patterns = {
  hours: { hour: number; label: string; event_count: number }[]
  weekdays: { label: string; event_count: number; top_artist: string | null }[]
  seasons: { label: string; event_count: number; top_artist: string | null; unique_artists: number }[]
  months: { label: string; event_count: number }[]
  peak_hour_insight: string
  peak_weekday_insight: string
}

export function PatternsPage() {
  const { data, error, loading } = useApi(() => api.patterns() as Promise<Patterns>, [])
  if (loading) return <LoadingBlock />
  if (error) return <StateMessage title="Patterns are unavailable" body={error} />
  if (!data?.hours?.some((row) => row.event_count > 0)) {
    return <StateMessage title="Not enough plays to see time of day" body="Temporal patterns need timestamps. Sync Spotify or open the demo." />
  }

  return (
    <div>
      <p className="text-[11px] tracking-[0.2em] uppercase text-muted">When and how you listen</p>
      <h2 className="text-4xl md:text-5xl font-medium tracking-tight mt-3">Listening patterns</h2>
      <div className="mt-6 space-y-3">
        <Insight>{data.peak_hour_insight}</Insight>
        <p className="text-lg text-muted">{data.peak_weekday_insight}</p>
      </div>
      <Section title="Hour of day">
        <Card>
          <HourChart data={data.hours} />
        </Card>
      </Section>
      <Section title="Day of week">
        <Card>
          <WeekdayChart data={data.weekdays} />
        </Card>
      </Section>
      <Section title="Season">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {data.seasons.map((season) => (
            <Card key={season.label}>
              <p className="text-sm text-muted">{season.label}</p>
              <p className="text-3xl font-medium mt-2">{season.event_count}</p>
              <p className="text-sm text-muted mt-2">{season.top_artist ? `Leans ${season.top_artist}` : '—'}</p>
            </Card>
          ))}
        </div>
      </Section>
    </div>
  )
}
