import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const projectsResponse = {
  home_root: 'C:\\Projects',
  projects: [
    {
      name: 'Real App',
      path: 'C:\\Projects\\real-app',
      description: 'Looks like an app folder',
      looks_like_project: true,
    },
  ],
};

const scanResponse = {
  repo: 'real-app',
  root_path: 'C:\\Projects\\real-app',
  head_commit: 'abc123',
  file_count: 12,
  modules: [
    {
      name: 'python-core',
      display_name: 'Main engine',
      purpose: 'Core application engine and main backend implementation.',
      simple_description: 'This is the part that does the main work of the app.',
      confidence_label: 'Strong guess',
      safety_label: 'Known area',
      files: ['app/core/engine.py'],
      tests: ['tests/core/test_engine.py'],
      confidence: 0.85,
      freshness: 'fresh',
      reachability: 'known',
      evidence: [],
    },
    {
      name: 'frontend',
      display_name: 'Screen and buttons',
      purpose: 'React user interface.',
      simple_description: 'This is what you see and click on.',
      confidence_label: 'Strong guess',
      safety_label: 'Known area',
      files: ['frontend/src/App.jsx'],
      tests: ['frontend/src/App.test.jsx'],
      confidence: 0.85,
      freshness: 'fresh',
      reachability: 'known',
      evidence: [],
    },
    {
      name: 'tests',
      display_name: 'Safety checks',
      purpose: 'Automated verification coverage.',
      simple_description: 'These files check whether the app still works after changes.',
      confidence_label: 'Medium guess',
      safety_label: 'Needs big-team check',
      files: ['tests/core/test_engine.py'],
      tests: ['tests/core/test_engine.py'],
      confidence: 0.65,
      freshness: 'fresh',
      reachability: 'unknown',
      evidence: [],
    },
  ],
  graph: {
    nodes: [
      {
        id: 'python-core',
        label: 'Main engine',
        description: 'This is the part that does the main work of the app.',
        safety_label: 'Known area',
        x: 46,
        y: 42,
        kind: 'module',
        layer: 'overview',
        module_id: 'python-core',
        files: ['app/core/engine.py'],
        metadata: {},
      },
      {
        id: 'tests',
        label: 'Safety checks',
        description: 'These files check whether the app still works after changes.',
        safety_label: 'Needs big-team check',
        x: 72,
        y: 28,
        kind: 'module',
        layer: 'overview',
        module_id: 'tests',
        files: ['tests/core/test_engine.py'],
        metadata: {},
      },
      {
        id: 'file:app/core/engine.py',
        label: 'engine.py',
        description: 'Python source file.',
        safety_label: 'Known area',
        x: 20,
        y: 20,
        kind: 'file',
        layer: 'files',
        module_id: 'python-core',
        files: ['app/core/engine.py'],
        metadata: { path: 'app/core/engine.py' },
      },
      ...Array.from({ length: 8 }, (_, index) => ({
        id: `file:app/core/dense-${index}.py`,
        label: `dense-${index}.py`,
        description: 'Python source file.',
        safety_label: 'Known area',
        x: 14,
        y: 86,
        kind: 'file',
        layer: 'files',
        module_id: 'python-core',
        files: [`app/core/dense-${index}.py`],
        metadata: { path: `app/core/dense-${index}.py` },
      })),
      {
        id: 'tool:npm:react',
        label: 'react',
        description: 'npm dependency',
        safety_label: 'External tool',
        x: 20,
        y: 20,
        kind: 'tool',
        layer: 'tools',
        module_id: 'frontend',
        files: ['package.json'],
        metadata: { manifest: 'package.json' },
      },
      {
        id: 'pipeline:npm:build',
        label: 'npm run build',
        description: 'vite build',
        safety_label: 'Known area',
        x: 20,
        y: 20,
        kind: 'script',
        layer: 'pipelines',
        module_id: 'frontend',
        files: ['package.json'],
        metadata: { source: 'package.json' },
      },
      {
        id: 'risk:tests',
        label: 'Safety checks needs review',
        description: 'reach is unknown',
        safety_label: 'Needs big-team check',
        x: 20,
        y: 20,
        kind: 'risk',
        layer: 'risk',
        module_id: 'tests',
        files: ['tests/core/test_engine.py'],
        metadata: { reasons: 'reach is unknown' },
      },
    ],
    links: [
      {
        source: 'tests',
        target: 'python-core',
        label: 'checks',
        reason: 'Mapped tests check this app part.',
        kind: 'test',
        layer: 'overview',
        files: ['tests/core/test_engine.py'],
      },
      {
        source: 'file:app/core/engine.py',
        target: 'tool:npm:react',
        label: 'imports',
        reason: 'File imports this external library.',
        kind: 'import',
        layer: 'tools',
        files: ['app/core/engine.py'],
      },
    ],
  },
};

function stubFetch() {
  const fetchMock = vi.fn((url: string) => {
    if (url.startsWith('/api/repo/scan')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(scanResponse) });
    }
    if (url === '/api/prompt/build') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          prompt: '$smac\nTarget: Screen and buttons',
          markdown: '$smac\nTarget: Screen and buttons',
          mode: 'diagnose_bug',
          mode_label: 'Diagnose bug',
          trigger_label: 'Pull trigger',
          destructive_actions_allowed: false,
        }),
      });
    }
    if (url === '/api/ai/map-review') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          markdown: '$mastermind\nReview this Project Atlas map.',
          prompt: '$mastermind\nReview this Project Atlas map.',
          trigger_label: 'Copy AI review prompt',
          destructive_actions_allowed: false,
          sends_code_automatically: false,
        }),
      });
    }
    if (url === '/api/projects') {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(projectsResponse) });
    }
    return Promise.reject(new Error(`Unexpected URL: ${url}`));
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('App', () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('auto-loads real project folders without fake sample rows', async () => {
    const fetchMock = stubFetch();

    render(<App />);

    expect(screen.getByText('Loading your project folders')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Real App')).toBeInTheDocument());
    expect(screen.queryByText('Sample API')).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith('/api/projects');
  });

  it('shows a visual project map after choosing a folder', async () => {
    stubFetch();

    render(<App />);
    await waitFor(() => expect(screen.getByText('Real App')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Real App'));

    await waitFor(() => expect(screen.getByText('Project map')).toBeInTheDocument());
    expect(screen.getByLabelText('Visual module map')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Main engine/ })).toBeInTheDocument();
    expect(screen.getByText('checks')).toBeInTheDocument();
    expect(screen.getByText('Pull trigger')).toBeInTheDocument();
  });

  it('shows deep map layers and aims SMAC through node module ids', async () => {
    const fetchMock = stubFetch();

    render(<App />);
    await waitFor(() => expect(screen.getByText('Real App')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Real App'));

    await waitFor(() => expect(screen.getByText('Project map')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Tools/ }));
    expect(screen.getByRole('button', { name: /react/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Pipelines/ }));
    expect(screen.getByRole('button', { name: /npm run build/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Files/ }));
    expect(screen.getByRole('button', { name: /engine.py/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Risk/ }));
    expect(screen.getByRole('button', { name: /Safety checks needs review/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Tools/ }));
    fireEvent.click(screen.getByRole('button', { name: /react/ }));
    fireEvent.click(screen.getByText('Pull trigger'));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
      '/api/prompt/build',
      expect.objectContaining({ body: expect.stringContaining('"module_name":"frontend"') }),
    ));
  });

  it('spreads dense layer nodes instead of stacking duplicated coordinates', async () => {
    stubFetch();

    render(<App />);
    await waitFor(() => expect(screen.getByText('Real App')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Real App'));

    await waitFor(() => expect(screen.getByText('Project map')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Files/ }));

    const denseNodes = screen.getAllByRole('button', { name: /dense-/ });
    const positions = new Set(denseNodes.map((node) => `${node.style.left}:${node.style.top}`));
    expect(denseNodes).toHaveLength(8);
    expect(positions.size).toBe(8);
  });

  it('builds an AI map-review prompt without sending code automatically', async () => {
    const fetchMock = stubFetch();

    render(<App />);
    await waitFor(() => expect(screen.getByText('Real App')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Real App'));

    await waitFor(() => expect(screen.getByText('Project map')).toBeInTheDocument());
    fireEvent.click(screen.getByText('AI review map'));

    await waitFor(() => expect(screen.getByLabelText('AI map review prompt')).toBeInTheDocument());
    expect(screen.getByText('AI prompt copied. Paste it into Claude or Codex.')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/ai/map-review',
      expect.objectContaining({ body: expect.stringContaining('real-app') }),
    );
  });
});
