import { Network, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';
import { type CSSProperties, type PointerEvent, useEffect, useMemo, useRef, useState } from 'react';
import type { AtlasModule, ModuleGraph, ModuleGraphNode } from '../types';

const LAYERS = [
  { id: 'workflow', label: 'Workflow' },
  { id: 'overview', label: 'Overview' },
  { id: 'pipelines', label: 'Pipelines' },
  { id: 'tools', label: 'Tools' },
  { id: 'files', label: 'Files' },
  { id: 'risk', label: 'Risk' },
];
const WORKFLOW_CANVAS_WIDTH = 1100;
const WORKFLOW_CANVAS_HEIGHT = 560;
const MIN_ZOOM = 0.8;
const MAX_ZOOM = 1.6;
const ZOOM_STEP = 0.2;

type Position = {
  x: number;
  y: number;
};

type DragState = {
  id: string;
  startClientX: number;
  startClientY: number;
  startX: number;
  startY: number;
} | null;

type ModuleMapProps = {
  graph: ModuleGraph | null;
  modules: AtlasModule[];
  selectedName: string;
  onSelect: (name: string) => void;
};

export function ModuleMap({ graph, modules, selectedName, onSelect }: ModuleMapProps) {
  const [activeLayer, setActiveLayer] = useState('overview');
  const [zoom, setZoom] = useState(1);
  const [nodePositions, setNodePositions] = useState<Record<string, Position>>({});
  const [dragging, setDragging] = useState<DragState>(null);
  const mapRef = useRef<HTMLDivElement | null>(null);
  const nodes = useMemo(() => (graph?.nodes.length ? graph.nodes : fallbackNodes(modules)), [graph, modules]);
  const links = graph?.links ?? [];
  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const counts = useMemo(() => layerCounts(nodes), [nodes]);
  const hasWorkflow = nodes.some((node) => node.layer === 'workflow');
  const isCanvas = activeLayer === 'overview' || activeLayer === 'workflow';
  const isWorkflow = activeLayer === 'workflow';
  const visibleLinks = isCanvas ? links.filter((link) => link.layer === activeLayer) : [];
  const visibleNodeIds = new Set(nodes.filter((node) => node.layer === activeLayer).map((node) => node.id));
  for (const link of visibleLinks) {
    if (nodeById.has(link.source)) visibleNodeIds.add(link.source);
    if (nodeById.has(link.target)) visibleNodeIds.add(link.target);
  }
  const visibleNodes = nodes.filter((node) => visibleNodeIds.has(node.id));
  const displayNodes = useMemo(() => summarizeLayerNodes(visibleNodes, activeLayer, modules), [visibleNodes, activeLayer, modules]);
  const positionedNodes = useMemo(
    () => displayNodes.map((node) => withPosition(node, nodePositions[node.id])),
    [displayNodes, nodePositions],
  );
  const displayNodeById = useMemo(() => new Map(positionedNodes.map((node) => [node.id, node])), [positionedNodes]);
  const activeLayerLabel = LAYERS.find((layer) => layer.id === activeLayer)?.label ?? 'Overview';
  const canvasStyle = isWorkflow
    ? { width: `${Math.round(WORKFLOW_CANVAS_WIDTH * zoom)}px`, height: `${Math.round(WORKFLOW_CANVAS_HEIGHT * zoom)}px` }
    : undefined;

  useEffect(() => {
    if (hasWorkflow) {
      setActiveLayer('workflow');
    }
  }, [hasWorkflow, graph]);

  useEffect(() => {
    setNodePositions({});
    setZoom(1);
  }, [graph]);

  function handlePointerDown(event: PointerEvent<HTMLButtonElement>, node: ModuleGraphNode) {
    if (!isCanvas) return;
    const position = nodePositions[node.id] ?? { x: node.x, y: node.y };
    setDragging({
      id: node.id,
      startClientX: event.clientX,
      startClientY: event.clientY,
      startX: position.x,
      startY: position.y,
    });
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function handlePointerMove(event: PointerEvent<HTMLButtonElement>) {
    if (!dragging) return;
    const rect = mapRef.current?.getBoundingClientRect();
    const width = rect && rect.width > 0 ? rect.width : 1000;
    const height = rect && rect.height > 0 ? rect.height : 600;
    const nextX = clamp(roundCoordinate(dragging.startX + ((event.clientX - dragging.startClientX) / width) * 100), 4, 96);
    const nextY = clamp(roundCoordinate(dragging.startY + ((event.clientY - dragging.startClientY) / height) * 100), 10, 90);
    setNodePositions((current) => ({ ...current, [dragging.id]: { x: nextX, y: nextY } }));
  }

  function handlePointerUp(event: PointerEvent<HTMLButtonElement>) {
    event.currentTarget.releasePointerCapture?.(event.pointerId);
    setDragging(null);
  }

  function resetWorkflowMap() {
    setNodePositions({});
    setZoom(1);
  }

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
      <div className="map-toolbar">
        <div className="map-summary">
          <strong>{activeLayerLabel}</strong>
          <span>{positionedNodes.length} {isCanvas ? 'nodes' : 'groups'} shown</span>
        </div>
        {isWorkflow ? (
          <div className="map-controls" aria-label="Workflow map controls">
            <button
              className="icon-action"
              type="button"
              aria-label="Zoom out workflow map"
              title="Zoom out"
              onClick={() => setZoom((value) => Math.max(MIN_ZOOM, roundCoordinate(value - ZOOM_STEP)))}
            >
              <ZoomOut size={16} aria-hidden="true" />
            </button>
            <button
              className="icon-action"
              type="button"
              aria-label="Reset workflow map"
              title="Reset map"
              onClick={resetWorkflowMap}
            >
              <RotateCcw size={16} aria-hidden="true" />
            </button>
            <button
              className="icon-action"
              type="button"
              aria-label="Zoom in workflow map"
              title="Zoom in"
              onClick={() => setZoom((value) => Math.min(MAX_ZOOM, roundCoordinate(value + ZOOM_STEP)))}
            >
              <ZoomIn size={16} aria-hidden="true" />
            </button>
          </div>
        ) : null}
      </div>
      <div className={`module-map${isCanvas ? ' canvas-map' : ' grouped-map'}${isWorkflow ? ' workflow-map' : ''}`} aria-label="Visual module map" ref={mapRef}>
        {isCanvas ? (
          <div className="map-canvas" style={canvasStyle}>
            <svg className={`map-lines${isWorkflow ? ' workflow-lines' : ''}`} viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              {isWorkflow ? (
                <defs>
                  <marker id="workflow-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
                    <path d="M 0 0 L 8 4 L 0 8 z" />
                  </marker>
                </defs>
              ) : null}
              {visibleLinks.map((link) => {
                const source = displayNodeById.get(link.source);
                const target = displayNodeById.get(link.target);
                if (!source || !target) return null;
                const midX = (source.x + target.x) / 2;
                const midY = (source.y + target.y) / 2;
                const path = `M ${source.x} ${source.y} C ${source.x + 7} ${source.y}, ${target.x - 7} ${target.y}, ${target.x} ${target.y}`;
                return (
                  <g key={`${link.source}-${link.target}-${link.label}`}>
                    {isWorkflow ? <path d={path} markerEnd="url(#workflow-arrow)" /> : <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} />}
                    {!isWorkflow ? <text x={midX} y={midY}>{link.label}</text> : null}
                  </g>
                );
              })}
            </svg>
            {positionedNodes.map((node) => renderNodeButton(
              node,
              selectedName,
              onSelect,
              'map-node',
              { left: `${node.x}%`, top: `${node.y}%` },
              { onPointerDown: handlePointerDown, onPointerMove: handlePointerMove, onPointerUp: handlePointerUp },
            ))}
          </div>
        ) : (
          <div className="map-grid">
            {positionedNodes.map((node) => renderNodeButton(node, selectedName, onSelect, 'map-card'))}
          </div>
        )}
        {!positionedNodes.length ? <div className="map-empty">No app parts found in this layer yet.</div> : null}
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
  interaction?: {
    onPointerDown: (event: PointerEvent<HTMLButtonElement>, node: ModuleGraphNode) => void;
    onPointerMove: (event: PointerEvent<HTMLButtonElement>) => void;
    onPointerUp: (event: PointerEvent<HTMLButtonElement>) => void;
  },
) {
  const targetName = node.kind === 'pipeline-stage' ? node.id : node.module_id ?? node.id;
  const selected = targetName === selectedName || node.id === selectedName;
  const nodeClass = `${className}${selected ? ' selected' : ''}${node.kind === 'pipeline-stage' ? ' pipeline-stage-node' : ''}`;
  return (
    <button
      className={nodeClass}
      type="button"
      key={node.id}
      onClick={() => onSelect(targetName)}
      onPointerDown={interaction ? (event) => interaction.onPointerDown(event, node) : undefined}
      onPointerMove={interaction?.onPointerMove}
      onPointerUp={interaction?.onPointerUp}
      style={style}
      aria-label={`${node.label}: ${node.description}`}
    >
      {node.kind === 'pipeline-stage' && node.metadata.sequence ? <span className="node-step">{node.metadata.sequence}</span> : null}
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
  if (layer === 'workflow' || layer === 'overview' || layer === 'risk') return nodes;
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
  if (kind === 'pipeline-stage') return 'Station';
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

function withPosition(node: ModuleGraphNode, position?: Position): ModuleGraphNode {
  if (!position) return node;
  return { ...node, x: position.x, y: position.y };
}

function roundCoordinate(value: number): number {
  return Math.round(value * 10) / 10;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
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
