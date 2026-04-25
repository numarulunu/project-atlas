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
      },
      {
        id: 'tests',
        label: 'Safety checks',
        description: 'These files check whether the app still works after changes.',
        safety_label: 'Needs big-team check',
        x: 72,
        y: 28,
      },
    ],
    links: [
      {
        source: 'tests',
        target: 'python-core',
        label: 'checks',
        reason: 'Mapped tests check this app part.',
      },
    ],
  },
};

function stubFetch() {
  const fetchMock = vi.fn((url: string) => {
    if (url.startsWith('/api/repo/scan')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(scanResponse) });
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
});
