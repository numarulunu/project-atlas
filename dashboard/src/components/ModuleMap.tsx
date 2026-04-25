import { Network } from 'lucide-react';
import type { AtlasModule, ModuleGraph, ModuleGraphNode } from '../types';

type ModuleMapProps = {
  graph: ModuleGraph | null;
  modules: AtlasModule[];
  selectedName: string;
  onSelect: (name: string) => void;
};

export function ModuleMap({ graph, modules, selectedName, onSelect }: ModuleMapProps) {
  const nodes = graph?.nodes.length ? graph.nodes : fallbackNodes(modules);
  const links = graph?.links ?? [];
  const nodeById = new Map(nodes.map((node) => [node.id, node]));

  return (
    <section className="panel map-panel" aria-label="Project module map">
      <div className="panel-title">
        <Network size={18} aria-hidden="true" />
        <h2>Project map</h2>
      </div>
      <div className="module-map" aria-label="Visual module map">
        <svg className="map-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {links.map((link) => {
            const source = nodeById.get(link.source);
            const target = nodeById.get(link.target);
            if (!source || !target) return null;
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
        {nodes.map((node) => {
          const selected = node.id === selectedName;
          return (
            <button
              className={`map-node${selected ? ' selected' : ''}`}
              type="button"
              key={node.id}
              onClick={() => onSelect(node.id)}
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
              aria-label={`${node.label}: ${node.description}`}
            >
              <span className="node-title">{node.label}</span>
              <span className="node-copy">{node.description}</span>
              <span className="node-chip">{node.safety_label}</span>
            </button>
          );
        })}
        {!nodes.length ? <div className="map-empty">No app parts found in this folder yet.</div> : null}
      </div>
      <div className="map-note">Click a node to aim SMAC at that exact part.</div>
    </section>
  );
}

function fallbackNodes(modules: AtlasModule[]): ModuleGraphNode[] {
  return modules.map((module, index) => ({
    id: module.name,
    label: module.display_name,
    description: module.simple_description,
    safety_label: module.safety_label,
    x: 20 + (index % 3) * 28,
    y: Math.min(78, 28 + Math.floor(index / 3) * 24),
  }));
}
