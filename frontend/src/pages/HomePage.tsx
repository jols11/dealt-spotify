import { EvolutionChart } from '../components/charts/Charts'
import { Card, Insight, LoadingBlock, Section, Stat, StateMessage } from '../components/ui/primitives'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { formatNumber } from '../utils/cn'

type Overview = {
  greeting: string
  headline: string
  period_label: string | null
  plays: number
  unique_artists: number
  unique_tracks: number
  session_count: number
  top_artist: { name: string; plays: number } | null
  strongest_transition: { source: string; target: string; count: number; probability: number } | null
  diversity_score: number
  diversity_interpretation: string
  top_artist_insight?: string
  strongest_transition_insight?: string | null
  rising?: { name: string; insight: string }[]
  user: { display_name: string; is_demo: boolean }
}

export function HomePage() {
  const { data, error, loading } = useApi(() => api.overview() as Promise<Overview>, [])
  const evolution = useApi(() => api.evolution() as Promise<{ weekly: { period: string; plays: number; unique_artists: number }[] }>, [])

  if (loading) return <LoadingBlock />
  if (error) return <StateMessage title="Could not load your listening" body={error} />
  if (!data || data.plays === 0) {
    return (
      <StateMessage
        title="No listening history yet"
        body="Refresh from Spotify to pull recently played tracks, or stay in demo mode to explore a full synthetic timeline."
      />
    )
  }

  return (
    <div>
      <p className="text-[11px] tracking-[0.2em] uppercase text-muted">{data.period_label}</p>
      <h2 className="text-4xl md:text-6xl font-medium tracking-tight mt-3 leading-[1.02]">{data.greeting}</h2>
      <p className="text-xl md:text-2xl text-muted mt-4">{data.headline}</p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 mt-12">
        <Stat label="Plays" value={formatNumber(data.plays)} hint="Recorded listening events in this library." />
        <Stat label="Artists" value={formatNumber(data.unique_artists)} />
        <Stat label="Tracks" value={formatNumber(data.unique_tracks)} />
        <Stat label="Sessions" value={formatNumber(data.session_count)} hint="Gaps longer than 30 minutes start a new session." />
      </div>

      <Section kicker="Listening evolution" title="How the volume of your listening moves">
        <Card>
          {evolution.loading ? (
            <LoadingBlock />
          ) : evolution.data?.weekly?.length ? (
            <EvolutionChart data={evolution.data.weekly} />
          ) : (
            <p className="text-muted">Not enough weeks to draw an evolution line yet.</p>
          )}
        </Card>
      </Section>

      <Section kicker="What stands out" title="A few things this history is saying">
        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <Insight>{data.top_artist_insight || 'A core artist has not emerged yet.'}</Insight>
            {data.top_artist ? (
              <p className="text-sm text-muted mt-4">{formatNumber(data.top_artist.plays)} plays</p>
            ) : null}
          </Card>
          <Card>
            <Insight>
              {data.strongest_transition_insight ||
                'There are not yet enough within-session handoffs to name a signature transition.'}
            </Insight>
          </Card>
          <Card className="md:col-span-2">
            <Insight>{data.diversity_interpretation}</Insight>
            <p className="text-sm text-muted mt-4">
              Normalized artist entropy {data.diversity_score.toFixed(2)} — 0 is a single artist, 1 is a perfectly even mix.
            </p>
          </Card>
        </div>
      </Section>
    </div>
  )
}
