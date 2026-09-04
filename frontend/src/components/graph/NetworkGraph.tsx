import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

type Node = {
  id: number
  name: string
  plays: number
  pagerank: number
  degree: number
  is_hub: boolean
}

type Edge = {
  source: number
  target: number
  count: number
  probability: number
  source_name: string
  target_name: string
}

type SimNode = Node & d3.SimulationNodeDatum
type SimLink = { source: SimNode | number | string; target: SimNode | number | string; count: number; probability: number }

export function NetworkGraph({
  nodes,
  edges,
  onSelect,
  selectedId,
}: {
  nodes: Node[]
  edges: Edge[]
  onSelect: (id: number | null) => void
  selectedId: number | null
}) {
  const ref = useRef<SVGSVGElement | null>(null)

  useEffect(() => {
    const svg = d3.select(ref.current)
    svg.selectAll('*').remove()
    if (!nodes.length) return

    const width = ref.current?.clientWidth || 800
    const height = 520
    svg.attr('viewBox', `0 0 ${width} ${height}`)

    const simNodes: SimNode[] = nodes.map((node) => ({ ...node }))
    const simLinks: SimLink[] = edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      count: edge.count,
      probability: edge.probability,
    }))

    const maxPlays = d3.max(simNodes, (d) => d.plays) || 1
    const radius = (d: SimNode) => 10 + Math.sqrt(d.plays / maxPlays) * 22

    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        'link',
        d3
          .forceLink<SimNode, SimLink>(simLinks)
          .id((d) => d.id)
          .distance(90)
          .strength(0.35),
      )
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide<SimNode>().radius((d) => radius(d) + 10))

    const link = svg
      .append('g')
      .selectAll('line')
      .data(simLinks)
      .enter()
      .append('line')
      .attr('stroke', '#cbbde0')
      .attr('stroke-opacity', 0.7)
      .attr('stroke-width', (d) => 1 + Math.log(d.count + 1))

    const node = svg
      .append('g')
      .selectAll('g')
      .data(simNodes)
      .enter()
      .append('g')
      .style('cursor', 'pointer')
      .on('click', (_, d) => onSelect(selectedId === d.id ? null : d.id))

    node
      .append('circle')
      .attr('r', radius)
      .attr('fill', (d) => (d.is_hub ? '#9d86c4' : '#f7f3fc'))
      .attr('stroke', (d) => (d.id === selectedId ? '#2c2740' : d.is_hub ? '#9d86c4' : '#d5c6ea'))
      .attr('stroke-width', (d) => (d.id === selectedId ? 2.5 : 1.2))

    node
      .append('text')
      .text((d) => d.name)
      .attr('font-size', 11)
      .attr('fill', '#2c2740')
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => radius(d) + 14)

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as SimNode).x || 0)
        .attr('y1', (d) => (d.source as SimNode).y || 0)
        .attr('x2', (d) => (d.target as SimNode).x || 0)
        .attr('y2', (d) => (d.target as SimNode).y || 0)
      node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    return () => {
      simulation.stop()
    }
  }, [nodes, edges, onSelect, selectedId])

  return <svg ref={ref} className="w-full h-[520px]" role="img" aria-label="Artist transition network" />
}
