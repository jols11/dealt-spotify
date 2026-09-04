import { EvolutionChart } from '../components/charts/Charts'
import { Card, Insight, LoadingBlock, Section, StateMessage } from '../components/ui/primitives'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'

export function EvolutionPage() {
  const { data, error, loading } = useApi(
    () =>
      api.evolution() as Promise<{
        weekly: { period: string; plays: number; unique_artists: number }[]
        rising: { name: string; insight: string; delta: number }[]
      }>,
    [],
  )

  if (loading) return <LoadingBlock />
  if (error) return <StateMessage title="Evolution is unavailable" body={error} />
  if (!data?.weekly?.length) {
    return <StateMessage title="Not enough history yet" body="Evolution compares weeks in your recorded listening. Sync more plays, or open the demo." />
  }

  const peak = [...data.weekly].sort((a, b) => b.plays - a.plays)[0]

  return (
    <div>
      <p className="text-[11px] tracking-[0.2em] uppercase text-muted">How your taste changes</p>
      <h2 className="text-4xl md:text-5xl font-medium tracking-tight mt-3">Listening evolution</h2>
      <div className="mt-6">
        <Insight>{`Your busiest week in this window is ${peak.period}, with ${peak.plays} plays.`}</Insight>
      </div>
      <Section title="Plays by week">
        <Card>
          <EvolutionChart data={data.weekly} />
        </Card>
      </Section>
      <Section kicker="Rising" title="Artists becoming more central">
        {data.rising?.length ? (
          <div className="grid md:grid-cols-2 gap-4">
            {data.rising.map((item) => (
              <Card key={item.name}>
                <p className="text-sm text-muted">Share increased {(item.delta * 100).toFixed(1)} pts</p>
                <p className="text-xl mt-2">{item.insight}</p>
              </Card>
            ))}
          </div>
        ) : (
          <StateMessage title="No clear risers" body="The first and second halves of this history look similar — or there is not enough volume to measure a lift." />
        )}
      </Section>
    </div>
  )
}
