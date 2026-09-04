import { Card, Insight, LoadingBlock, Section, StateMessage } from '../components/ui/primitives'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'

type Rec = {
  artist_id: number
  artist_name: string
  score: number
  reason: string
  last_played_days_ago: number | null
  historical_plays: number
}

export function RecommendationsPage() {
  const { data, error, loading } = useApi(() => api.recommendations(), [])
  if (loading) return <LoadingBlock />
  if (error) return <StateMessage title="Recommendations unavailable" body={error} />
  const items = (data?.items || []) as Rec[]
  if (!items.length) {
    return (
      <StateMessage
        title="Nothing to revisit yet"
        body="This is a transparent heuristic: historically frequent artists that have gone quiet, especially neighbors of artists you still play. It is not Spotify Radio and it is not a trained model."
      />
    )
  }

  return (
    <div>
      <p className="text-[11px] tracking-[0.2em] uppercase text-muted">What's worth revisiting?</p>
      <h2 className="text-4xl md:text-5xl font-medium tracking-tight mt-3">Return to these artists</h2>
      <div className="mt-6">
        <Insight>
          Ranked from your own history: past share, how long they have been quiet, and whether you usually reach them
          from artists you still play.
        </Insight>
      </div>
      <Section title="Why each one appears">
        <div className="space-y-4">
          {items.map((item) => (
            <Card key={item.artist_id}>
              <div className="flex justify-between gap-4">
                <h3 className="text-2xl font-medium">{item.artist_name}</h3>
                <p className="text-sm text-muted">{item.historical_plays} plays</p>
              </div>
              <p className="mt-3 text-[#3d3750]">{item.reason}</p>
            </Card>
          ))}
        </div>
      </Section>
    </div>
  )
}
