import { Card, Insight, LoadingBlock, Section, StateMessage } from '../components/ui/primitives'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'

type Taste = {
  diversity: {
    unique_artists: number
    unique_tracks: number
    artist_entropy: number
    normalized_entropy: number
    herfindahl_index: number
    top_artist_share: number
    top_artist_name: string | null
    repeat_rate: number
    transition_diversity: number
    interpretation: string
  }
  top_artists: { id: number; name: string; plays: number; share: number }[]
  clusters: { cluster_id: number; label: string; interpretation: string; artists: { name: string; plays: number }[] }[]
  similarity: { persona: string; cosine_similarity: number; caveat: string }[]
}

export function TastePage() {
  const { data, error, loading } = useApi(() => api.taste() as Promise<Taste>, [])
  if (loading) return <LoadingBlock />
  if (error) return <StateMessage title="Taste profile unavailable" body={error} />
  if (!data?.top_artists?.length) {
    return <StateMessage title="No taste profile yet" body="Diversity and clusters need a spread of artists. Open the demo for a full example." />
  }

  const d = data.diversity
  return (
    <div>
      <p className="text-[11px] tracking-[0.2em] uppercase text-muted">Your listening profile</p>
      <h2 className="text-4xl md:text-5xl font-medium tracking-tight mt-3">Taste</h2>
      <div className="mt-6">
        <Insight>{d.interpretation}</Insight>
      </div>

      <Section title="Diversity, with the math in plain language">
        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <p className="text-sm text-muted">Artist entropy</p>
            <p className="text-3xl mt-2">{d.artist_entropy.toFixed(2)}</p>
            <p className="text-sm text-muted mt-2">H = −Σ pᵢ log₂(pᵢ). Higher means listening is spread across more artists.</p>
          </Card>
          <Card>
            <p className="text-sm text-muted">Top-artist share</p>
            <p className="text-3xl mt-2">{(d.top_artist_share * 100).toFixed(0)}%</p>
            <p className="text-sm text-muted mt-2">{d.top_artist_name} of all recorded plays.</p>
          </Card>
          <Card>
            <p className="text-sm text-muted">Repeat rate</p>
            <p className="text-3xl mt-2">{(d.repeat_rate * 100).toFixed(0)}%</p>
            <p className="text-sm text-muted mt-2">Share of plays that are not first-time tracks in this library.</p>
          </Card>
        </div>
      </Section>

      <Section title="Artists you return to">
        <div className="space-y-3">
          {data.top_artists.map((artist, index) => (
            <div key={artist.id} className="flex items-center gap-4">
              <span className="text-muted w-6">{String(index + 1).padStart(2, '0')}</span>
              <div className="flex-1">
                <div className="flex justify-between text-sm mb-1">
                  <span>{artist.name}</span>
                  <span className="text-muted">{(artist.share * 100).toFixed(1)}%</span>
                </div>
                <div className="h-[6px] rounded-full bg-line">
                  <div className="h-full rounded-full bg-accent" style={{ width: `${Math.max(artist.share * 100, 2)}%` }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section kicker="Exploratory" title="Taste clusters">
        <p className="text-muted max-w-2xl mb-6 -mt-2">
          Groups are built from your own timing and frequency vectors, then labeled playfully. They are not scientific
          genre identities and they are not trained on Spotify audio.
        </p>
        {data.clusters.length ? (
          <div className="grid md:grid-cols-2 gap-4">
            {data.clusters.map((cluster) => (
              <Card key={cluster.cluster_id}>
                <p className="text-xl font-medium">{cluster.label}</p>
                <p className="text-sm text-muted mt-2">{cluster.interpretation}</p>
                <p className="mt-4 text-sm">{cluster.artists.map((a) => a.name).join(' · ')}</p>
              </Card>
            ))}
          </div>
        ) : (
          <StateMessage title="Too few artists to cluster" body="Clustering needs several artists with enough plays to form a feature vector." />
        )}
      </Section>

      {data.similarity.length ? (
        <Section title="Pattern similarity (synthetic personas)">
          <p className="text-muted mb-4 -mt-2">This compares artist-share vectors, not people.</p>
          <div className="space-y-3">
            {data.similarity.map((row) => (
              <div key={row.persona} className="flex justify-between border-b border-line pb-3">
                <div>
                  <p>{row.persona}</p>
                  <p className="text-sm text-muted">{row.caveat}</p>
                </div>
                <p className="tabular-nums">{row.cosine_similarity.toFixed(2)}</p>
              </div>
            ))}
          </div>
        </Section>
      ) : null}
    </div>
  )
}
