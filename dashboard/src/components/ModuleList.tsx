import { GitBranch } from 'lucide-react';
import type { AtlasModule } from '../types';

type ModuleListProps = {
  modules: AtlasModule[];
  selectedName: string;
  onSelect: (name: string) => void;
};

export function ModuleList({ modules, selectedName, onSelect }: ModuleListProps) {
  return (
    <section className="panel module-panel" aria-label="Module map">
      <div className="panel-title">
        <GitBranch size={18} aria-hidden="true" />
        <h2>Parts of the app</h2>
      </div>
      <div className="module-list">
        {modules.map((module) => {
          const selected = module.name === selectedName;
          return (
            <button
              className={`module-row${selected ? ' selected' : ''}`}
              type="button"
              key={module.name}
              onClick={() => onSelect(module.name)}
            >
              <span className="module-main">
                <span className="module-name">{module.display_name}</span>
                <span className="module-purpose">{module.simple_description}</span>
                <span className="technical-name">Code name: {module.name}</span>
              </span>
              <span className="module-meta">
                <span>{module.confidence_label}</span>
                <span>{module.safety_label}</span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}