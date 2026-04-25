import { ClipboardCheck, Crosshair, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { buildSniperPrompt } from '../api';
import type { AtlasModule, PromptMode } from '../types';

const ACTIONS: Array<{ mode: PromptMode; label: string; description: string }> = [
  { mode: 'diagnose_bug', label: 'Diagnose bug', description: 'Find what is broken and where to look first.' },
  { mode: 'audit_quality', label: 'Audit quality', description: 'Check this part for quality and reliability risks.' },
  { mode: 'cleanup_risk', label: 'Cleanup risk', description: 'Find stale-looking code without deleting anything.' },
];

type SniperTriggerProps = {
  repoPath: string;
  module: AtlasModule;
};

export function SniperTrigger({ repoPath, module }: SniperTriggerProps) {
  const [mode, setMode] = useState<PromptMode>('diagnose_bug');
  const [prompt, setPrompt] = useState('');
  const [status, setStatus] = useState('Ready to build a sniper prompt. Nothing runs until you click.');
  const [loading, setLoading] = useState(false);

  async function handleTrigger() {
    setLoading(true);
    setStatus('Building sniper prompt...');
    try {
      const result = await buildSniperPrompt(repoPath, module.name, mode);
      setPrompt(result.prompt);
      await copyPrompt(result.prompt);
      setStatus('Prompt copied. Paste it into Claude or Codex and send it.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Prompt build failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel trigger-panel" aria-label="SMAC trigger">
      <div className="panel-title">
        <Crosshair size={18} aria-hidden="true" />
        <h2>Aim SMAC</h2>
      </div>
      <div className="target-card">
        <span>Target</span>
        <strong>{module.display_name}</strong>
        <p>{module.simple_description}</p>
      </div>
      <div className="action-grid" aria-label="Choose diagnostic type">
        {ACTIONS.map((action) => (
          <button
            className={`action-card${mode === action.mode ? ' selected' : ''}`}
            type="button"
            key={action.mode}
            onClick={() => setMode(action.mode)}
          >
            <strong>{action.label}</strong>
            <span>{action.description}</span>
          </button>
        ))}
      </div>
      <button className="trigger-button" type="button" onClick={handleTrigger} disabled={loading}>
        {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <ClipboardCheck size={18} aria-hidden="true" />}
        <span>Pull trigger</span>
      </button>
      <p className="trigger-status">{status}</p>
      {prompt ? (
        <div className="prompt-output">
          <div className="prompt-output-header">
            <strong>Sniper prompt ready</strong>
            <span>Hidden context is included inside this prompt.</span>
          </div>
          <textarea readOnly value={prompt} aria-label="Generated sniper prompt" />
        </div>
      ) : null}
    </section>
  );
}

async function copyPrompt(prompt: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(prompt);
  }
}