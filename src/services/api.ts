import {
  ImageForensicResult,
  AudioForensicResult,
  VideoForensicResult,
  FusionForensicResult,
  SamplesCatalog,
  SessionHistoryItem,
} from '../types/forensic';

async function parseJsonResponse<T>(res: Response): Promise<T> {
  const payload = await res.json().catch(() => ({}));
  if (!res.ok || payload.status === 'error') {
    throw new Error(payload.error || `Request failed with HTTP ${res.status}`);
  }
  return payload as T;
}

export async function fetchSamplesCatalog(): Promise<SamplesCatalog> {
  const res = await fetch('/api/samples');
  const json = await parseJsonResponse<{status: string; samples: SamplesCatalog}>(res);
  return json.samples;
}

export async function fetchRecentSessions(): Promise<SessionHistoryItem[]> {
  const res = await fetch('/api/sessions');
  const json = await parseJsonResponse<{status: string; sessions: SessionHistoryItem[]}>(res);
  return json.sessions;
}

export async function analyzeUploadedFile<T>(
  endpoint: '/api/analyze-image' | '/api/analyze-audio' | '/api/analyze-video',
  file: File,
): Promise<T> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(endpoint, {
    method: 'POST',
    body: form,
  });
  const json = await parseJsonResponse<{status: string; session_id: string; data: T}>(res);
  return {...json.data, session_id: json.session_id};
}

export async function analyzeSampleAsset<T>(
  modality: 'image' | 'audio' | 'video',
  filename: string,
): Promise<T> {
  const res = await fetch('/api/analyze-sample', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({modality, filename}),
  });
  const json = await parseJsonResponse<{status: string; session_id: string; data: T}>(res);
  return {...json.data, session_id: json.session_id};
}

export async function fuseSessions(params: {
  image_session_id?: string;
  audio_session_id?: string;
  video_session_id?: string;
}): Promise<FusionForensicResult> {
  const res = await fetch('/api/fuse', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(params),
  });
  const json = await parseJsonResponse<{
    status: string;
    session_id: string;
    data: FusionForensicResult;
  }>(res);
  return {...json.data, session_id: json.session_id};
}

export async function askForensicChat(
  mode: 'image' | 'audio' | 'video' | 'fusion',
  sessionId: string,
  question: string,
): Promise<string> {
  const res = await fetch(`/api/chat/${mode}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({session_id: sessionId, question}),
  });
  const json = await parseJsonResponse<{status: string; answer: string}>(res);
  return json.answer;
}

export function getReportDownloadUrl(sessionId: string): string {
  return `/api/report/${encodeURIComponent(sessionId)}`;
}

export type AnyForensicResult =
  | ImageForensicResult
  | AudioForensicResult
  | VideoForensicResult
  | FusionForensicResult;
