import { Network } from 'lucide-react';
import { type CSSProperties, useMemo, useState } from 'react';
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
  const visibleLinks = activeLayer === 'overview' ? links.filter((link) => link.layer === activeLayer) : [];
  const visibleNodeIds = new Set(nodes.filter((node) => node.layer === activeLayer).map((node) => node.id));
  for (const link of visibleLinks) {
    if (nodeById.has(link.source)) visibleNodeIds.add(link.source);
    if (nodeById.has(link.target)) visibleNodeIds.add(link.target);
  }
  const visibleNodes = nodes.filter((node) => visibleNodeIds.has(node.id));
  const displayNodes = useMemo(() => summarizeLayerNodes(visibleNodes, activeLayer, modules), [visibleNodes, activeLayer, modules]);
  const displayNodeById = useMemo(() => new Map(displayNodes.map((node) => [node.id, node])), [displayNodes]);
  const activeLayerLabel = LAYERS.find((layer) => layer.id === activeLayer)?.label ?? 'Overview';
  const isOverview = activeLayer === 'overview';

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
        <span>{displayNodes.length} {isOverview ? 'nodes' : 'groups'} shown</span>
      </div>
      <div className={`module-map${isOverview ? '' : ' grouped-map'}`} aria-label="Visual module map">
        {isOverview ? (
          <>
            <svg className="map-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              {visibleLinks.map((link) => {
                const source = displayNodeById.get(link.source);
                const target = displayNodeById.get(link.target);
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
            {displayNodes.map((node) => renderNodeButton(node, selectedName, onSelect, 'map-node', { left: `${node.x}%`, top: `${node.y}%` }))}
          </>
        ) : (
          <div className="map-grid">
            {displayNodes.map((node) => renderNodeButton(node, selectedName, onSelect, 'map-card'))}
          </div>
        )}
        {!displayNodes.length ? <div className="map-empty">No app parts found in this layer yet.</div> : null}
      </div>
      <div className="map-note">Click a node to aim SMAC at that exact part.</div>
    </section>
  );
}

function renderNodeButton(
  node: ModuleGraphNode,
  selectedName: string,
  onSelect: (name: string) => void,
  className: string,
  style?: CSSProperties,
) {
  const targetName = node.module_id ?? node.id;
  const selected = targetName === selectedName || node.id === selectedName;
  return (
    <button
      className={`${className}${selected ? ' selected' : ''}`}
      type="button"
      key={node.id}
      onClick={() => onSelect(targetName)}
      style={style}
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
}

function summarizeLayerNodes(nodes: ModuleGraphNode[], layer: string, modules: AtlasModule[]): ModuleGraphNode[] {
  if (layer === 'overview' || layer === 'risk') return nodes;
  if (layer === 'files') return summarizeGroups(nodes, modules, fileGroupKey, fileGroupNode);
  if (layer === 'tools') return summarizeGroups(nodes, modules, toolGroupKey, toolGroupNode);
  if (layer === 'pipelines') return summarizeGroups(nodes, modules, pipelineGroupKey, pipelineGroupNode);
  return nodes;
}

function summarizeGroups(
  nodes: ModuleGraphNode[],
  modules: AtlasModule[],
  keyFor: (node: ModuleGraphNode) => string,
  makeNode: (key: string, nodes: ModuleGraphNode[], modules: AtlasModule[]) => ModuleGraphNode,
): ModuleGraphNode[] {
  const grouped = new Map<string, ModuleGraphNode[]>();
  for (const node of nodes) {
    const key = keyFor(node);
    grouped.set(key, [...(grouped.get(key) ?? []), node]);
  }
  return Array.from(grouped.entries()).map(([key, items]) => makeNode(key, items, modules));
}

function fileGroupKey(node: ModuleGraphNode): string {
  const path = node.files[0] ?? node.metadata.path ?? node.label;
  return `${node.module_id ?? 'unknown'}:${folderLabel(path)}`;
}

function fileGroupNode(key: string, nodes: ModuleGraphNode[], modules: AtlasModule[]): ModuleGraphNode {
  const [moduleId, folder] = splitGroupKey(key);
  const files = unique(nodes.flatMap((node) => node.files));
  return groupNode({
    id: `group:files:${key}`,
    label: folder,
    description: `${files.length} files in ${moduleDisplayName(moduleId, modules)}`,
    kind: 'file-group',
    layer: 'files',
    moduleId,
    files,
    nodes,
  });
}

function toolGroupKey(node: ModuleGraphNode): string {
  return `${node.module_id ?? 'unknown'}:${node.id.split(':')[1] ?? 'tool'}`;
}

function toolGroupNode(key: string, nodes: ModuleGraphNode[], modules: AtlasModule[]): ModuleGraphNode {
  const [moduleId, ecosystem] = splitGroupKey(key);
  const files = unique(nodes.flatMap((node) => node.files));
  return groupNode({
    id: `group:tools:${key}`,
    label: `${ecosystem} tools`,
    description: `${nodes.length} tools or libraries used by ${moduleDisplayName(moduleId, modules)}`,
    kind: 'tool-group',
    layer: 'tools',
    moduleId,
    files,
    nodes,
  });
}

function pipelineGroupKey(node: ModuleGraphNode): string {
  return `${node.module_id ?? 'unknown'}:${pipelineLabel(node.kind)}`;
}

function pipelineGroupNode(key: string, nodes: ModuleGraphNode[], modules: AtlasModule[]): ModuleGraphNode {
  const [moduleId, label] = splitGroupKey(key);
  const files = unique(nodes.flatMap((node) => node.files));
  return groupNode({
    id: `group:pipelines:${key}`,
    label,
    description: `${nodes.length} routes or commands for ${moduleDisplayName(moduleId, modules)}`,
    kind: 'pipeline-group',
    layer: 'pipelines',
    moduleId,
    files,
    nodes,
  });
}

function groupNode(input: {
  id: string;
  label: string;
  description: string;
  kind: string;
  layer: string;
  moduleId: string;
  files: string[];
  nodes: ModuleGraphNode[];
}): ModuleGraphNode {
  return {
    id: input.id,
    label: input.label,
    description: input.description,
    safety_label: groupSafety(input.nodes),
    x: 50,
    y: 50,
    kind: input.kind,
    layer: input.layer,
    module_id: input.moduleId === 'unknown' ? null : input.moduleId,
    files: input.files,
    metadata: { count: String(input.nodes.length) },
  };
}

function folderLabel(path: string): string {
  const parts = path.split('/').filter(Boolean);
  if (parts.length <= 1) return 'Project root';
  return parts.slice(0, Math.min(2, parts.length - 1)).join('/');
}

function pipelineLabel(kind: string): string {
  if (kind === 'route') return 'Routes';
  if (kind === 'entrypoint') return 'Start points';
  return 'Commands';
}

function splitGroupKey(key: string): [string, string] {
  const index = key.indexOf(':');
  return index === -1 ? [key, key] : [key.slice(0, index), key.slice(index + 1)];
}

function moduleDisplayName(moduleId: string, modules: AtlasModule[]): string {
  return modules.find((module) => module.name === moduleId)?.display_name ?? 'this area';
}

function groupSafety(nodes: ModuleGraphNode[]): string {
  return nodes.some((node) => node.safety_label !== 'Known area') ? 'Needs big-team check' : 'Known area';
}

function unique(items: string[]): string[] {
  return Array.from(new Set(items));
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
  if (kind === 'file-group') return 'Files';
  if (kind === 'tool-group') return 'Tools';
  if (kind === 'pipeline-group') return 'Workflow';
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
