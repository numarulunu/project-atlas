import { FolderOpen } from 'lucide-react';

type RepoHeaderProps = {
  repoName: string;
  fileCount: number;
  backendUnavailable: boolean;
};

export function RepoHeader({ repoName, fileCount, backendUnavailable }: RepoHeaderProps) {
  return (
    <header className="repo-header">
      <div>
        <p className="eyebrow">Read-only command center</p>
        <h1>Project Atlas</h1>
        <p className="safety-line">No auto-fix. No auto-delete. No auto-reorganize.</p>
      </div>
      <div className="repo-status" aria-label="Selected folder status">
        <FolderOpen size={20} aria-hidden="true" />
        <span>{repoName}</span>
        <strong>{fileCount ? `${fileCount} files read` : 'No folder scanned yet'}</strong>
      </div>
      {backendUnavailable ? <div className="notice">Backend unavailable. You can still paste a folder path, then retry.</div> : null}
    </header>
  );
}