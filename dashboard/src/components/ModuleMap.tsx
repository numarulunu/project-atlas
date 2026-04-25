import { Network } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { AtlasModule, ModuleGraph, ModuleGraphNode } from '../types';

const LAYERS = [
  { id: 'overview', label: 'Overview' },
  { id: 'pipelines', label: 'Pipelines' },
  { id: 'tools', label: 'Tools' },
  { id: 'files', label: 'Files' },
  { id: 'risk', label: 'Risk' },
];

type ModuleMapProps = {
  graph: ModuleGraph | null;
  modules: AtlasModule[];
  selectedName: string;
  onSelect: (name: string) => void;
};

export function ModuleMap({ graph, modules, selectedName, onSelect }: ModuleMapProps) {
  const [activeLayer, setActiveLayer] = useState('overview');
  const nodes = useMemo(() => (graph?.nodes.length ? graph.nodes : fallbackNodes(modules)), [graph, modules]);
  const links = graph?.links ?? [];
  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const counts = useMemo(() => layerCounts(nodes), [nodes]);
  const visibleLinks = links.filter((link) => link.layer === activeLayer);
  const visibleNodeIds = new Set(nodes.filter((node) => node.layer === activeLayer).map((node) => node.id));
  for (const link of visibleLinks) {
    if (nodeById.has(link.source)) visibleNodeIds.add(link.source);
    if (nodeById.has(link.target)) visibleNodeIds.add(link.target);
  }
  const visibleNodes = nodes.filter((node) => visibleNodeIds.has(node.id));
  const activeLayerLabel = LAYERS.find((layer) => layer.id === activeLayer)?.label ?? 'Overview';

  return (
    <section className="panel map-panel" aria-label="Project module map">
      <div className="panel-title">
        <Network size={18} aria-hidden="true" />
        <h2>Project map</h2>
      </div>
      <div className="layer-tabs" aria-label="Map layers">
        {LAYERS.map((layer) => (
          <button
            className={`layer-tab${activeLayer === layer.id ? ' selected' : ''}`}
            type="button"
            key={layer.id}
            onClick={() => setActiveLayer(layer.id)}
          >
            <span>{layer.label}</span>
            <strong>{counts[layer.id] ?? 0}</strong>
          </button>
        ))}
      </div>
      <div className="map-summary">
        <strong>{activeLayerLabel}</strong>
        <span>{visibleNodes.length} nodes shown</span>
      </div>
      <div className="module-map" aria-label="Visual module map">
        <svg className="map-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {visibleLinks.map((link) => {
            const source = nodeById.get(link.source);
            const target = nodeById.get(link.target);
            if (!source || !target || !visibleNodeIds.has(source.id) || !visibleNodeIds.has(target.id)) return null;
            const midX = (source.x + target.x) / 2;
            const midY = (source.y + target.y) / 2;
            return (
              <g key={`${link.source}-${link.target}-${link.label}`}>
                <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} />
                <text x={midX} y={midY}>{link.label}</text>
              </g>
            );
          })}
        </svg>
        {visibleNodes.map((node) => {
          const targetName = node.module_id ?? node.id;
          const selected = targetName === selectedName || node.id === selectedName;
          return (
            <button
              className={`map-node${selected ? ' selected' : ''}`}
              type="button"
              key={node.id}
              onClick={() => onSelect(targetName)}
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
              aria-label={`${node.label}: ${node.description}`}
            >
              <span className="node-title">{node.label}</span>
              <span className="node-copy">{node.description}</span>
              <span className="node-chip-row">
                <span className="node-chip">{kindLabel(node.kind)}</span>
                <span className="node-chip">{node.safety_label}</span>
              </span>
            </button>
          );
        })}
        {!visibleNodes.length ? <div className="map-empty">No app parts found in this layer yet.</div> : null}
      </div>
      <div className="map-note">Click a node to aim SMAC at that exact part.</div>
    </section>
  );
}

function layerCounts(nodes: ModuleGraphNode[]): Record<string, number> {
  return nodes.reduce<Record<string, number>>((counts, node) => {
    counts[node.layer] = (counts[node.layer] ?? 0) + 1;
    return counts;
  }, {});
}

function kindLabel(kind: string): string {
  if (kind === 'module') return 'App part';
  if (kind === 'file') return 'File';
  if (kind === 'tool') return 'Tool';
  if (kind === 'script') return 'Command';
  if (kind === 'route') return 'Route';
  if (kind === 'entrypoint') return 'Start point';
  if (kind === 'risk') return 'Risk';
  return kind;
}

function fallbackNodes(modules: AtlasModule[]): ModuleGraphNode[] {
  return modules.map((module, index) => ({
    id: module.name,
    label: module.display_name,
    description: module.simple_description,
    safety_label: module.safety_label,
    x: 20 + (index % 3) * 28,
    y: Math.min(78, 28 + Math.floor(index / 3) * 24),
    kind: 'module',
    layer: 'overview',
    module_id: module.name,
    files: module.files,
    metadata: { technical_name: module.name },
  }));
}
