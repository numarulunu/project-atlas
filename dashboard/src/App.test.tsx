import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const scanResponse = {
  repo: 'sample-api',
  root_path: 'C:\\Projects\\sample-api',
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
  ],
};

describe('App', () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('opens on a folder picker instead of scanning a project automatically', () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    render(<App />);

    expect(screen.getByText('Project Atlas')).toBeInTheDocument();
    expect(screen.getByText('Choose the folder for your app')).toBeInTheDocument();
    expect(screen.getByText('Atlas will only read this folder. It will not change, delete, or move anything.')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalledWith('/api/repo/scan');
  });

  it('shows a trigger UI after choosing a folder instead of coder evidence panels', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url.startsWith('/api/repo/scan')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(scanResponse) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ home_root: '', projects: [] }) });
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<App />);
    fireEvent.click(screen.getByText('Sample API'));

    await waitFor(() => expect(screen.getByText('Pull trigger')).toBeInTheDocument());
    expect(screen.getByText('Diagnose bug')).toBeInTheDocument();
    expect(screen.queryByText('Why Atlas grouped it this way')).not.toBeInTheDocument();
    expect(screen.queryByText('Files Atlas would aim at')).not.toBeInTheDocument();
  });
});
