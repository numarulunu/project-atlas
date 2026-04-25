import type { AiMapReviewResponse, PacketResponse, ProjectListResponse, PromptBuildResponse, PromptMode, ScanResponse } from './types';

export async function listProjects(): Promise<ProjectListResponse> {
  const response = await fetch('/api/projects');
  if (!response.ok) throw new Error('Could not load folders');
  return response.json();
}

export async function scanRepo(repoPath: string): Promise<ScanResponse> {
  const response = await fetch(`/api/repo/scan?repo_path=${encodeURIComponent(repoPath)}`);
  if (!response.ok) throw new Error('Scan failed');
  return response.json();
}

export async function buildSniperPrompt(repoPath: string, moduleName: string, mode: PromptMode): Promise<PromptBuildResponse> {
  const response = await fetch('/api/prompt/build', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_path: repoPath, module_name: moduleName, mode }),
  });
  if (!response.ok) throw new Error('Prompt build failed');
  return response.json();
}

export async function previewPacket(repoPath: string, moduleName: string, question: string): Promise<PacketResponse> {
  const response = await fetch('/api/packet/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_path: repoPath, module_name: moduleName, question }),
  });
  if (!response.ok) throw new Error('Packet preview failed');
  return response.json();
}

export async function buildAiMapReviewPrompt(repoPath: string): Promise<AiMapReviewResponse> {
  const response = await fetch('/api/ai/map-review', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_path: repoPath }),
  });
  if (!response.ok) throw new Error('AI review prompt failed');
  return response.json();
}
