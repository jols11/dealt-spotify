import { useMemo, useState } from 'react'
import { NetworkGraph } from '../components/graph/NetworkGraph'
import { Card, Insight, LoadingBlock, Section, StateMessage } from '../components/ui/primitives'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'

type Network = {
  insight: string
  nodes: { id: number; name: string; plays: number; pagerank: number; degree: number; is_hub: boolean }[]
  edges: { source: number; target: number; count: number; probability: number; source_name: string; target_name: string }[]
  transitions: { source: string; target: string; count: number; probability: number; source_id: number; target_id: number }[]
}

export function NetworkPage() {
  const [minCount, setMinCount] = useState(2)
  const [selected, setSelected] = useState<number | null>(null)
  const { data, error, loading } = useApi(() => api.transitions({ min_count: minCount }) as Promise<Network>, [minCount])

  const neighborhood = useMemo(() => {
    if (!data || selected == null) return data?.edges || []
    return data.edges.filter((edge) => edge.source === selected || edge.target === selected)
  }, [data, selected])

  if (loading) return <LoadingBlock />
  if (error) return <StateMessage title="The network could not be built" body={error} />
  if (!data?.nodes?.length) {
    return (
      <StateMessage
        title="The graph is still empty"
        body="Artist transitions only count when one artist follows another inside the same listening session. A single play, or a library of isolated tracks, will not draw a network."
      />
    )
  }

  const selectedNode = data.nodes.find((node) => node.id === selected)

  return (
    <div>
      <p className="text-[11px] tracking-[0.2em] uppercase text-muted">Who connects your listening?</p>
      <h2 className="text-4xl md:text-5xl font-medium tracking-tight mt-3">Your music network</h2>
      <div className="mt-6">
        <Insight>{data.insight}</Insight>
      </div>

      <div className="flex flex-wrap gap-2 mt-8">
        {[2, 3, 5].map((value) => (
          <button
            key={value}
            onClick={() => setMinCount(value)}
            className={`px-4 py-2 rounded-full text-sm ${minCount === value ? 'bg-ink text-paper' : 'bg-card border border-line'}`}
          >
            Min {value} handoffs
          </button>
        ))}
      </div>

      <Section title="Meaningful connections only">
        <Card className="overflow-hidden">
          <p className="text-sm text-muted mb-4">
            Burgundy nodes are hubs. Click an artist to isolate incoming and outgoing handoffs. Self-repeats are hidden
            so the picture stays readable.
          </p>
          <NetworkGraph nodes={data.nodes} edges={data.edges} selectedId={selected} onSelect={setSelected} />
        </Card>
      </Section>

      <Section title={selectedNode ? `Around ${selectedNode.name}` : 'Strongest handoffs'}>
        <div className="space-y-3">
          {(selected ? neighborhood : data.edges).slice(0, 12).map((edge) => (
            <div key={`${edge.source}-${edge.target}`} className="flex items-baseline justify-between gap-4 border-b border-line pb-3">
              <p>
                You most often move from <span className="font-medium">{edge.source_name}</span> to{' '}
                <span className="font-medium">{edge.target_name}</span>
              </p>
              <p className="text-sm text-muted whitespace-nowrap">
                {edge.count} times · {(edge.probability * 100).toFixed(0)}% of exits
              </p>
            </div>
          ))}
        </div>
      </Section>
    </div>
  )
}
