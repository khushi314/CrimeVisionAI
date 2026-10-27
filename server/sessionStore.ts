import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

const REPO_ROOT = process.cwd();
export const SESSIONS_DIR = path.join(REPO_ROOT, 'data', 'sessions');
export const UPLOADS_DIR = path.join(REPO_ROOT, 'data', 'uploads');
export const TEMP_FRAMES_DIR = path.join(REPO_ROOT, 'data', 'temp_frames');
export const SAMPLES_DIR = path.join(REPO_ROOT, 'data', 'samples');
export const REPORTS_DIR = path.join(REPO_ROOT, 'outputs', 'reports');

for (const dir of [SESSIONS_DIR, UPLOADS_DIR, TEMP_FRAMES_DIR, SAMPLES_DIR, REPORTS_DIR]) {
  fs.mkdirSync(dir, {recursive: true});
}

export interface SessionSummary {
  session_id: string;
  mode: string;
  created_at_utc: string;
  file_name?: string;
  location?: string;
}

function sanitizeId(rawId: string): string {
  return rawId.replace(/[^a-zA-Z0-9_-]/g, '');
}

function sessionFilePath(sessionId: string): string {
  const safe = sanitizeId(sessionId);
  if (!safe) {
    throw new Error('Invalid session_id');
  }
  return path.join(SESSIONS_DIR, `session_${safe}.json`);
}

export function createSession(data: Record<string, unknown>, customId?: string): string {
  const sessionId = customId ? sanitizeId(customId) : crypto.randomUUID();
  const innerData = {
    session_id: sessionId,
    created_at_utc: new Date().toISOString(),
    ...data,
  };
  const envelope = {
    session_id: sessionId,
    timestamp: Date.now() / 1000,
    data: innerData,
  };
  fs.writeFileSync(sessionFilePath(sessionId), JSON.stringify(envelope, null, 2), 'utf-8');
  return sessionId;
}

export function getSession(sessionId: string): Record<string, any> | null {
  try {
    const target = sessionFilePath(sessionId);
    if (!fs.existsSync(target)) return null;
    const raw = JSON.parse(fs.readFileSync(target, 'utf-8'));
    return raw.data ? raw.data : raw;
  } catch {
    return null;
  }
}

export function updateSession(
  sessionId: string,
  patch: Record<string, unknown>,
): Record<string, any> {
  const existing = getSession(sessionId) || {
    session_id: sessionId,
    created_at_utc: new Date().toISOString(),
  };
  const updated = {
    ...existing,
    ...patch,
    updated_at_utc: new Date().toISOString(),
  };
  createSession(updated, sessionId);
  return updated;
}

export function listSessions(limit = 25): SessionSummary[] {
  if (!fs.existsSync(SESSIONS_DIR)) return [];
  const files = fs
    .readdirSync(SESSIONS_DIR)
    .filter((f) => f.startsWith('session_') && f.endsWith('.json'))
    .map((f) => ({
      name: f,
      mtime: fs.statSync(path.join(SESSIONS_DIR, f)).mtimeMs,
    }))
    .sort((a, b) => b.mtime - a.mtime)
    .slice(0, limit);

  const items: SessionSummary[] = [];
  for (const file of files) {
    try {
      const parsed = JSON.parse(fs.readFileSync(path.join(SESSIONS_DIR, file.name), 'utf-8'));
      const raw = parsed.data ? parsed.data : parsed;
      items.push({
        session_id: parsed.session_id || raw.session_id,
        mode: raw.mode || 'unknown',
        created_at_utc:
          raw.created_at_utc ||
          (parsed.timestamp ? new Date(parsed.timestamp * 1000).toISOString() : ''),
        file_name: raw.file_name,
        location: raw.location || raw.scene_intelligence?.location,
      });
    } catch {
      // Skip malformed session file
    }
  }
  return items;
}

export function computeSha256Buffer(buffer: Buffer): string {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}
