import { ClipboardCheck, Loader2, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { buildAiMapReviewPrompt } from '../api';

type AiMapReviewProps = {
  repoPath: string;
};

export function AiMapReview({ repoPath }: AiMapReviewProps) {
  const [prompt, setPrompt] = useState('');
  const [status, setStatus] = useState('Build an AI review prompt from the map facts. Nothing is sent automatically.');
  const [loading, setLoading] = useState(false);

  async function handleReview() {
    setLoading(true);
    setStatus('Building AI map review prompt...');
    try {
      const result = await buildAiMapReviewPrompt(repoPath);
      setPrompt(result.prompt);
      await copyPrompt(result.prompt);
      setStatus('AI prompt copied. Paste it into Claude or Codex.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'AI review prompt failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel ai-review-panel" aria-label="AI map review">
      <div className="panel-title">
        <Sparkles size={18} aria-hidden="true" />
        <h2>AI map review</h2>
      </div>
      <p className="ai-review-copy">Ask AI to improve the map names, groups, missing links, and uncertainty flags from Atlas facts.</p>
      <button className="secondary-action" type="button" onClick={handleReview} disabled={loading}>
        {loading ? <Loader2 className="spin" size={17} aria-hidden="true" /> : <ClipboardCheck size={17} aria-hidden="true" />}
        <span>AI review map</span>
      </button>
      <p className="trigger-status">{status}</p>
      {prompt ? <textarea className="ai-review-output" readOnly value={prompt} aria-label="AI map review prompt" /> : null}
    </section>
  );
}

async function copyPrompt(prompt: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(prompt);
  }
}
