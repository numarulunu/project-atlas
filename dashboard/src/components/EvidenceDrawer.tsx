import { FileText } from 'lucide-react';
import type { AtlasModule } from '../types';

type EvidenceDrawerProps = {
  module: AtlasModule;
};

export function EvidenceDrawer({ module }: EvidenceDrawerProps) {
  const evidence = module.evidence ?? [];
  return (
    <section className="panel evidence-panel" aria-label="Evidence drawer">
      <div className="panel-title">
        <FileText size={18} aria-hidden="true" />
        <h2>What this part means</h2>
      </div>
      <div className="metrics-grid">
        <Metric label="How sure?" value={module.confidence_label} />
        <Metric label="Safety" value={module.safety_label} />
        <Metric label="Files in this part" value={String(module.files.length)} />
        <Metric label="Safety checks" value={String(module.tests.length)} />
      </div>
      <p className="module-summary">{module.simple_description}</p>
      <div className="plain-note">
        <strong>Simple rule:</strong> Tell SMAC to stay inside this part unless the evidence clearly points somewhere else.
      </div>
      <div className="file-scope">
        <h3>Files Atlas would aim at</h3>
        <ul>
          {module.files.slice(0, 12).map((file) => (
            <li key={file}>{file}</li>
          ))}
        </ul>
      </div>
      <div className="evidence-list">
        <h3>Why Atlas grouped it this way</h3>
        {evidence.length ? (
          evidence.slice(0, 8).map((item) => (
            <div className="signal-row" key={`${item.source_file}:${item.source_line}:${item.quote}`}>
              <span>{item.kind}</span>
              <strong>{item.source_file}:{item.source_line ?? 0}</strong>
              <p>{item.quote}</p>
            </div>
          ))
        ) : (
          <p className="empty-state">No direct evidence captured.</p>
        )}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}