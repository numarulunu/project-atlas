import { ClipboardList, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { previewPacket } from '../api';

type PacketPreviewProps = {
  repoPath: string;
  moduleName: string;
  question: string;
};

export function PacketPreview({ repoPath, moduleName, question }: PacketPreviewProps) {
  const [markdown, setMarkdown] = useState('SMAC Packet');
  const [needsFullSmac, setNeedsFullSmac] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handlePreview() {
    setLoading(true);
    setError('');
    try {
      const packet = await previewPacket(repoPath, moduleName, question);
      setMarkdown(packet.markdown);
      setNeedsFullSmac(packet.needs_full_smac);
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : 'Packet preview failed');
      setMarkdown('SMAC Packet');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel packet-panel" aria-label="Packet preview">
      <div className="panel-title">
        <ClipboardList size={18} aria-hidden="true" />
        <h2>SMAC Packet</h2>
      </div>
      <div className="packet-controls">
        <button className="primary-action" type="button" onClick={handlePreview} disabled={loading}>
          {loading ? <Loader2 className="spin" size={17} aria-hidden="true" /> : <ClipboardList size={17} aria-hidden="true" />}
          <span>Preview packet</span>
        </button>
        <span className="blocked-pill">Destructive actions: blocked</span>
      </div>
      {needsFullSmac ? <div className="notice tight">Full SMAC required</div> : null}
      {error ? <div className="error-line">{error}</div> : null}
      <pre className="packet-text">{markdown}</pre>
    </section>
  );
}