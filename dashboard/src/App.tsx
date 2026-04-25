import { Folder, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { listProjects, scanRepo } from './api';
import { AiMapReview } from './components/AiMapReview';
import { ModuleMap } from './components/ModuleMap';
import { RepoHeader } from './components/RepoHeader';
import { SniperTrigger } from './components/SniperTrigger';
import type { AtlasModule, ModuleGraph, ProjectCandidate } from './types';
import './styles.css';

export default function App() {
  const [projects, setProjects] = useState<ProjectCandidate[]>([]);
  const [modules, setModules] = useState<AtlasModule[]>([]);
  const [graph, setGraph] = useState<ModuleGraph | null>(null);
  const [selectedName, setSelectedName] = useState('');
  const [repoPath, setRepoPath] = useState('');
  const [manualPath, setManualPath] = useState('');
  const [repoName, setRepoName] = useState('Choose a folder');
  const [fileCount, setFileCount] = useState(0);
  const [backendUnavailable, setBackendUnavailable] = useState(false);
  const [loadingFolders, setLoadingFolders] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoadingFolders(true);
    listProjects()
      .then((result) => {
        if (!active) return;
        setProjects(result.projects);
        setBackendUnavailable(false);
      })
      .catch(() => {
        if (!active) return;
        setProjects([]);
        setBackendUnavailable(true);
      })
      .finally(() => {
        if (active) setLoadingFolders(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleScan(path: string) {
    const trimmedPath = path.trim();
    if (!trimmedPath) {
      setError('Choose a folder first.');
      return;
    }
    setScanning(true);
    setError('');
    try {
      const result = await scanRepo(trimmedPath);
      setModules(result.modules);
      setGraph(result.graph);
      setRepoPath(result.root_path);
      setRepoName(result.repo);
      setFileCount(result.file_count);
      setSelectedName(result.modules[0]?.name ?? '');
      setBackendUnavailable(false);
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : 'Scan failed');
    } finally {
      setScanning(false);
    }
  }

  const selectedModule = useMemo(
    () => modules.find((module) => module.name === selectedName) ?? modules[0],
    [modules, selectedName],
  );
  const hasScan = Boolean(repoPath);

  return (
    <main className="app-shell">
      <RepoHeader repoName={repoName} fileCount={fileCount} backendUnavailable={backendUnavailable} />
      {!hasScan ? (
        <section className="picker-layout" aria-label="Choose project folder">
          <div className="panel picker-panel">
            <div className="panel-title">
              <Folder size={18} aria-hidden="true" />
              <h2>Choose the folder for your app</h2>
            </div>
            <p className="picker-copy">Atlas will only read this folder. It will not change, delete, or move anything.</p>
            <div className="path-entry">
              <label htmlFor="manual-path">Paste a folder path</label>
              <div className="path-row">
                <input
                  id="manual-path"
                  value={manualPath}
                  onChange={(event) => setManualPath(event.target.value)}
                  placeholder="Example: C:\\path\\to\\your\\project"
                />
                <button className="primary-action" type="button" onClick={() => handleScan(manualPath)} disabled={scanning}>
                  <Search size={17} aria-hidden="true" />
                  <span>{scanning ? 'Reading folder' : 'Read folder'}</span>
                </button>
              </div>
            </div>
            <div className="project-list-header">
              <h3>Your project folders</h3>
              <span>{loadingFolders ? 'Loading' : `${projects.length} found`}</span>
            </div>
            <div className="project-list">
              {loadingFolders ? <div className="project-empty">Loading your project folders</div> : null}
              {!loadingFolders && backendUnavailable ? (
                <div className="project-empty">Could not load local projects. Paste a folder path above.</div>
              ) : null}
              {!loadingFolders && !backendUnavailable && !projects.length ? (
                <div className="project-empty">No project folders found. Paste one above.</div>
              ) : null}
              {projects.map((project) => (
                <button className="project-row" type="button" key={project.path} onClick={() => handleScan(project.path)} disabled={scanning}>
                  <span>
                    <strong>{project.name}</strong>
                    <small>{project.description}</small>
                  </span>
                  <code>{project.path}</code>
                </button>
              ))}
            </div>
            {error ? <div className="error-line">{error}</div> : null}
          </div>
          <div className="panel legend-panel">
            <h2>What happens next</h2>
            <div className="legend-item">
              <strong>Pick a folder</strong>
              <span>Atlas reads the project and draws the main app parts.</span>
            </div>
            <div className="legend-item">
              <strong>Click a node</strong>
              <span>The map chooses the exact app part you want to inspect.</span>
            </div>
            <div className="legend-item">
              <strong>Pull trigger</strong>
              <span>Atlas copies a ready SMAC prompt. You paste it into Claude or Codex and send it.</span>
            </div>
          </div>
        </section>
      ) : (
        <div className="dashboard-grid">
          <div className="map-column">
            <ModuleMap graph={graph} modules={modules} selectedName={selectedModule?.name ?? selectedName} onSelect={setSelectedName} />
            <AiMapReview repoPath={repoPath} />
          </div>
          {selectedModule ? (
            <SniperTrigger repoPath={repoPath} module={selectedModule} />
          ) : (
            <section className="panel trigger-panel" aria-label="SMAC trigger">
              <h2>Aim SMAC</h2>
              <p className="trigger-status">No app part is mapped yet. Try another folder or paste a more specific project path.</p>
            </section>
          )}
        </div>
      )}
    </main>
  );
}
