import { Folder, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { listProjects, scanRepo } from './api';
import { ModuleList } from './components/ModuleList';
import { RepoHeader } from './components/RepoHeader';
import { SniperTrigger } from './components/SniperTrigger';
import type { AtlasModule, ProjectCandidate } from './types';
import './styles.css';

const FALLBACK_MODULES: AtlasModule[] = [
  {
    name: 'python-core',
    display_name: 'Main engine',
    purpose: 'Core application engine and main backend implementation.',
    simple_description: 'This is the part that does the main work of the app.',
    confidence_label: 'Strong guess',
    safety_label: 'Known area',
    files: ['app/core/engine.py', 'app/core/governor.py'],
    tests: ['tests/core/test_engine.py'],
    confidence: 0.85,
    freshness: 'fallback',
    reachability: 'known',
    evidence: [],
  },
  {
    name: 'frontend',
    display_name: 'Screen and buttons',
    purpose: 'React user interface.',
    simple_description: 'This is what you see and click on.',
    confidence_label: 'Medium guess',
    safety_label: 'Known area',
    files: ['frontend/src/App.jsx'],
    tests: [],
    confidence: 0.78,
    freshness: 'fallback',
    reachability: 'known',
    evidence: [],
  },
  {
    name: 'docs',
    display_name: 'Notes and instructions',
    purpose: 'Project documentation and operating notes.',
    simple_description: 'These files explain what the project is and how to use it.',
    confidence_label: 'Weak guess',
    safety_label: 'Needs big-team check',
    files: ['README.md', 'tool_registry.md'],
    tests: [],
    confidence: 0.5,
    freshness: 'fallback',
    reachability: 'unknown',
    evidence: [],
  },
];

const FALLBACK_PROJECTS: ProjectCandidate[] = [
  {
    name: 'Sample API',
    path: '~/Projects/sample-api',
    description: 'Looks like an app folder',
    looks_like_project: true,
  },
  {
    name: 'Sample Dashboard',
    path: '~/Projects/sample-dashboard',
    description: 'Looks like an app folder',
    looks_like_project: true,
  },
];

export default function App() {
  const [projects, setProjects] = useState<ProjectCandidate[]>(FALLBACK_PROJECTS);
  const [modules, setModules] = useState<AtlasModule[]>([]);
  const [selectedName, setSelectedName] = useState('');
  const [repoPath, setRepoPath] = useState('');
  const [manualPath, setManualPath] = useState('');
  const [repoName, setRepoName] = useState('Choose a folder');
  const [fileCount, setFileCount] = useState(0);
  const [backendUnavailable, setBackendUnavailable] = useState(false);
  const [loadingFolders, setLoadingFolders] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (import.meta.env.MODE === 'test') return;
    let active = true;
    setLoadingFolders(true);
    listProjects()
      .then((result) => {
        if (!active) return;
        setProjects(result.projects.length ? result.projects : FALLBACK_PROJECTS);
        setBackendUnavailable(false);
      })
      .catch(() => {
        if (!active) return;
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
      const nextModules = result.modules.length ? result.modules : FALLBACK_MODULES;
      setModules(nextModules);
      setRepoPath(result.root_path);
      setRepoName(result.repo);
      setFileCount(result.file_count);
      setSelectedName(nextModules[0]?.name ?? '');
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
  const hasScan = Boolean(selectedModule && repoPath);

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
              <h3>Common project folders</h3>
              <span>{loadingFolders ? 'Loading folders' : `${projects.length} found`}</span>
            </div>
            <div className="project-list">
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
              <span>Atlas reads the project and splits it into plain-English app parts.</span>
            </div>
            <div className="legend-item">
              <strong>Aim SMAC</strong>
              <span>Choose the part and the kind of check you want.</span>
            </div>
            <div className="legend-item">
              <strong>Pull trigger</strong>
              <span>Atlas copies a ready SMAC prompt. You paste it into Claude or Codex and send it.</span>
            </div>
          </div>
        </section>
      ) : (
        <div className="dashboard-grid">
          <ModuleList modules={modules} selectedName={selectedModule.name} onSelect={setSelectedName} />
          <SniperTrigger repoPath={repoPath} module={selectedModule} />
        </div>
      )}
    </main>
  );
}
