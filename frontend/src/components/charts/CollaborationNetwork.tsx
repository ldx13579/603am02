import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import type { CollaborationGraph } from '../../types';

interface Props {
  data: CollaborationGraph;
}

export default function CollaborationNetwork({ data }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || !data.nodes.length) return;

    const maxCommits = Math.max(...data.nodes.map(n => n.commit_count), 1);
    const maxWeight = Math.max(...data.edges.map(e => e.weight), 1);

    const elements: cytoscape.ElementDefinition[] = [
      ...data.nodes.map(node => ({
        data: {
          id: node.id,
          label: node.id.length > 16 ? node.id.slice(0, 14) + '...' : node.id,
          commit_count: node.commit_count,
          size: 30 + (node.commit_count / maxCommits) * 60,
          isCluster: (node as any).is_cluster || false,
        },
      })),
      ...data.edges.map((edge, i) => ({
        data: {
          id: `e${i}`,
          source: edge.source,
          target: edge.target,
          weight: edge.weight,
          width: 1 + (edge.weight / maxWeight) * 6,
          shared_files: edge.shared_files.join(', '),
        },
      })),
    ];

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#4A90D9',
            'label': 'data(label)',
            'width': 'data(size)',
            'height': 'data(size)',
            'font-size': '10px',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'color': '#333',
            'text-wrap': 'ellipsis',
            'text-max-width': '80px',
          },
        },
        {
          selector: 'node[?isCluster]',
          style: {
            'background-color': '#95A5A6',
            'shape': 'diamond',
            'border-width': 2,
            'border-color': '#7F8C8D',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(width)',
            'line-color': '#999',
            'curve-style': 'bezier',
            'opacity': 0.6,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationDuration: 500,
        nodeRepulsion: () => 8000,
        idealEdgeLength: () => 120,
        gravity: 0.3,
      } as cytoscape.CoseLayoutOptions,
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    });

    cy.on('mouseover', 'node', (event) => {
      const node = event.target;
      const isCluster = node.data('isCluster');
      node.style('background-color', isCluster ? '#E67E22' : '#E74C3C');
    });

    cy.on('mouseout', 'node', (event) => {
      const node = event.target;
      const isCluster = node.data('isCluster');
      node.style('background-color', isCluster ? '#95A5A6' : '#4A90D9');
    });

    cyRef.current = cy;

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [data]);

  if (!data.nodes.length) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>
        No collaboration data available (single-author repository)
      </div>
    );
  }

  const clusterNode = data.nodes.find((n: any) => n.is_cluster);

  return (
    <div style={{ position: 'relative' }}>
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '500px',
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          background: '#fafafa',
        }}
      />
      <div style={{ marginTop: 8, fontSize: 12, color: '#666', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <span>Nodes: {data.nodes.length} developers</span>
        <span>Edges: {data.edges.length} collaborations</span>
        <span>(node size = commit count, edge thickness = shared files)</span>
        {clusterNode && (
          <span style={{ color: '#95A5A6' }}>
            Diamond node = collapsed minor contributors
          </span>
        )}
      </div>
    </div>
  );
}
