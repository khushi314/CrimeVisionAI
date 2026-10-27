import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import express from 'express';
import multer from 'multer';
import {createServer as createViteServer} from 'vite';
import {
  UPLOADS_DIR,
  SAMPLES_DIR,
  createSession,
  getSession,
  updateSession,
  listSessions,
  computeSha256Buffer,
} from './server/sessionStore';
import {
  ForensicAnalysisError,
  analyzeImageForensics,
  analyzeAudioForensics,
  analyzeVideoForensics,
  fuseForensicSessions,
  queryForensicChat,
  generateForensicPdfBuffer,
} from './server/geminiForensicEngine';

const PORT = Number(process.env.PORT) || 3000;
const FLASK_BACKEND_URL = process.env.FLASK_BACKEND_URL?.trim() || '';

const ALLOWED_EXTENSIONS: Record<'image' | 'audio' | 'video', Set<string>> = {
  image: new Set(['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']),
  audio: new Set(['.wav', '.mp3', '.m4a', '.ogg', '.flac']),
  video: new Set(['.mp4', '.avi', '.mov', '.mkv', '.webm']),
};

function sanitizeFileName(rawName: string): string {
  const base = path.basename(rawName || 'evidence.bin');
  return base.replace(/[^a-zA-Z0-9._-]/g, '_');
}

function validateExtension(filename: string, modality: 'image' | 'audio' | 'video'): string | null {
  if (!filename) return `Missing filename for ${modality} upload.`;
  const ext = path.extname(filename).toLowerCase();
  if (!ALLOWED_EXTENSIONS[modality].has(ext)) {
    return `Unsupported ${modality} format '${ext || 'unknown'}'. Allowed: ${Array.from(
      ALLOWED_EXTENSIONS[modality],
    ).join(', ')}`;
  }
  return null;
}

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {fileSize: 50 * 1024 * 1024},
});

async function startServer() {
  const app = express();
  app.use(express.json({limit: '10mb'}));

  // Serve synthetic sample assets and runtime uploaded files for media playback/inspection
  app.use('/samples', express.static(SAMPLES_DIR));
  app.use('/uploads', express.static(UPLOADS_DIR));

  // Optional proxy pass-through when student runs Python Flask backend on port 5000
  if (FLASK_BACKEND_URL) {
    app.use('/api', async (req, res, next) => {
      // Keep /api/samples handled locally for UI sample drawer metadata
      if (req.path === '/samples' || req.path === '/analyze-sample') {
        return next();
      }
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 1500);
        const ping = await fetch(`${FLASK_BACKEND_URL}/api/health`, {signal: controller.signal});
        clearTimeout(timeout);
        if (!ping.ok) return next();

        const targetUrl = `${FLASK_BACKEND_URL}/api${req.url}`;
        const headers: Record<string, string> = {};
        if (req.headers['content-type']) {
          headers['content-type'] = req.headers['content-type'];
        }
        const init: RequestInit = {
          method: req.method,
          headers,
        };
        if (req.method !== 'GET' && req.method !== 'HEAD' && req.headers['content-type']?.includes('application/json')) {
          init.body = JSON.stringify(req.body);
        } else if (req.method !== 'GET' && req.method !== 'HEAD') {
          // Multipart uploads handled directly if not JSON
          return next();
        }
        const upstream = await fetch(targetUrl, init);
        res.status(upstream.status);
        const contentType = upstream.headers.get('content-type') || '';
        res.setHeader('Content-Type', contentType);
        const buf = Buffer.from(await upstream.arrayBuffer());
        return res.send(buf);
      } catch {
        return next();
      }
    });
  }

  app.get('/api/health', (_req, res) => {
    res.json({
      status: 'healthy',
      service: 'CrimeVision AI Gateway',
      version: '1.0.0',
      modules: {
        vision: 'ready',
        audio: 'ready',
        video: 'ready',
        fusion: 'ready',
        chat: 'ready',
        report: 'ready',
      },
    });
  });

  app.get('/api/samples', (_req, res) => {
    res.json({
      status: 'success',
      samples: {
        image: [
          {
            id: 'office_scene',
            label: 'Case 01 — Office Suite Disturbance',
            filename: 'synthetic_office_scene.jpg',
            url: '/samples/images/synthetic_office_scene.jpg',
            description: '1280×720 staged office room with desk, laptop, overturned chair, floor silhouette & knife prop.',
          },
          {
            id: 'retail_store',
            label: 'Case 02 — Retail Display Counter',
            filename: 'synthetic_retail_store_scene.jpg',
            url: '/samples/images/synthetic_retail_store_scene.jpg',
            description: '1280×720 staged retail counter with glass case, standing figure, handbag & dropped necklace.',
          },
        ],
        audio: [
          {
            id: 'witness_store',
            label: 'Witness Statement — Maple Ave Store Robbery',
            filename: 'synthetic_witness_store_robbery.wav',
            url: '/samples/audio/synthetic_witness_store_robbery.wav',
            description: '20s witness recording corroborated with Case 02 retail store scene (EN / HI / TE / FR).',
          },
          {
            id: 'witness_office',
            label: 'Witness Statement — Suite 304 Office Crash',
            filename: 'synthetic_witness_office_burglary.wav',
            url: '/samples/audio/synthetic_witness_office_burglary.wav',
            description: '16s security witness statement corroborated with Case 01 office scene (EN / HI / TE / FR).',
          },
        ],
        video: [
          {
            id: 'cctv_store',
            label: 'CAM-04 — Retail Store Counter Sequence (10s)',
            filename: 'synthetic_store_cctv.mp4',
            url: '/samples/videos/synthetic_store_cctv.mp4',
            description: '10s CCTV sequence: idle counter, subject entry (00:02), bag removal (00:05) & rapid exit.',
          },
          {
            id: 'cctv_corridor',
            label: 'CAM-01 — Office Corridor Routine Walk (8s)',
            filename: 'synthetic_corridor_cctv.mp4',
            url: '/samples/videos/synthetic_corridor_cctv.mp4',
            description: '8s baseline CCTV sequence demonstrating NORMAL ACTIVITY classification.',
          },
        ],
      },
    });
  });

  app.post('/api/analyze-sample', async (req, res) => {
    try {
      const {modality, filename} = req.body || {};
      if (!['image', 'audio', 'video'].includes(modality) || !filename) {
        return res.status(400).json({status: 'error', error: 'Specify valid modality and sample filename.'});
      }
      const subdir = modality === 'image' ? 'images' : modality === 'audio' ? 'audio' : 'videos';
      const safeFile = sanitizeFileName(filename);
      const targetPath = path.join(SAMPLES_DIR, subdir, safeFile);
      if (!fs.existsSync(targetPath)) {
        return res.status(404).json({
          status: 'error',
          error: `Sample file '${safeFile}' not found. Run 'python3 scripts/generate_samples.py' first.`,
        });
      }

      const raw = fs.readFileSync(targetPath);
      const sha256 = computeSha256Buffer(raw);
      const mediaUrl = `/samples/${subdir}/${safeFile}`;

      let result: Record<string, any>;
      if (modality === 'image') {
        result = await analyzeImageForensics(targetPath, safeFile, sha256);
      } else if (modality === 'audio') {
        result = await analyzeAudioForensics(targetPath, safeFile, sha256);
      } else {
        result = await analyzeVideoForensics(targetPath, safeFile, sha256);
      }

      result.media_url = mediaUrl;
      const sessionId = createSession(result);
      result.session_id = sessionId;
      return res.json({status: 'success', session_id: sessionId, data: result});
    } catch (err: any) {
      const code = err instanceof ForensicAnalysisError ? err.statusCode : 500;
      return res.status(code).json({status: 'error', error: err?.message || 'Sample analysis failed.'});
    }
  });

  app.post('/api/analyze-image', upload.single('file'), async (req, res) => {
    if (!req.file) {
      return res.status(400).json({status: 'error', error: "Missing 'file' field in multipart upload."});
    }
    const errMsg = validateExtension(req.file.originalname, 'image');
    if (errMsg) {
      return res.status(400).json({status: 'error', error: errMsg});
    }

    const storedName = `${Date.now()}_${sanitizeFileName(req.file.originalname)}`;
    const savedPath = path.join(UPLOADS_DIR, storedName);
    try {
      const sha256 = computeSha256Buffer(req.file.buffer);
      fs.writeFileSync(savedPath, req.file.buffer);

      const result = await analyzeImageForensics(savedPath, req.file.originalname, sha256);
      result.media_url = `/uploads/${storedName}`;
      const sessionId = createSession(result, req.body?.session_id);
      result.session_id = sessionId;
      return res.json({status: 'success', session_id: sessionId, data: result});
    } catch (err: any) {
      if (fs.existsSync(savedPath)) {
        fs.rmSync(savedPath, {force: true});
      }
      const code = err instanceof ForensicAnalysisError ? err.statusCode : 502;
      return res.status(code).json({status: 'error', error: err?.message || 'Image analysis failed.'});
    }
  });

  app.post('/api/analyze-audio', upload.single('file'), async (req, res) => {
    if (!req.file) {
      return res.status(400).json({status: 'error', error: "Missing 'file' field in multipart upload."});
    }
    const errMsg = validateExtension(req.file.originalname, 'audio');
    if (errMsg) {
      return res.status(400).json({status: 'error', error: errMsg});
    }

    try {
      const sha256 = computeSha256Buffer(req.file.buffer);
      const storedName = `${Date.now()}_${sanitizeFileName(req.file.originalname)}`;
      const savedPath = path.join(UPLOADS_DIR, storedName);
      fs.writeFileSync(savedPath, req.file.buffer);

      const result = await analyzeAudioForensics(savedPath, req.file.originalname, sha256);
      result.media_url = `/uploads/${storedName}`;
      const sessionId = createSession(result, req.body?.session_id);
      result.session_id = sessionId;
      return res.json({status: 'success', session_id: sessionId, data: result});
    } catch (err: any) {
      return res.status(500).json({status: 'error', error: err?.message || 'Audio analysis failed.'});
    }
  });

  app.post('/api/analyze-video', upload.single('file'), async (req, res) => {
    if (!req.file) {
      return res.status(400).json({status: 'error', error: "Missing 'file' field in multipart upload."});
    }
    const errMsg = validateExtension(req.file.originalname, 'video');
    if (errMsg) {
      return res.status(400).json({status: 'error', error: errMsg});
    }

    try {
      const sha256 = computeSha256Buffer(req.file.buffer);
      const storedName = `${Date.now()}_${sanitizeFileName(req.file.originalname)}`;
      const savedPath = path.join(UPLOADS_DIR, storedName);
      fs.writeFileSync(savedPath, req.file.buffer);

      const result = await analyzeVideoForensics(savedPath, req.file.originalname, sha256);
      result.media_url = `/uploads/${storedName}`;
      const sessionId = createSession(result, req.body?.session_id);
      result.session_id = sessionId;
      return res.json({status: 'success', session_id: sessionId, data: result});
    } catch (err: any) {
      return res.status(500).json({status: 'error', error: err?.message || 'Video analysis failed.'});
    }
  });

  app.post('/api/upload', upload.array('files', 10), (req, res) => {
    const uploadedFiles = (req.files as Express.Multer.File[]) || [];
    if (uploadedFiles.length === 0) {
      return res.status(400).json({status: 'error', error: 'No evidence files provided.'});
    }
    const caseId = req.body?.case_id || crypto.randomUUID();
    const savedItems: Array<Record<string, any>> = [];

    for (const file of uploadedFiles) {
      const ext = path.extname(file.originalname).toLowerCase();
      const modality = ALLOWED_EXTENSIONS.image.has(ext)
        ? 'image'
        : ALLOWED_EXTENSIONS.audio.has(ext)
        ? 'audio'
        : ALLOWED_EXTENSIONS.video.has(ext)
        ? 'video'
        : null;
      if (!modality) {
        return res.status(400).json({status: 'error', error: `Unsupported file type '${file.originalname}'.`});
      }
      const sha256 = computeSha256Buffer(file.buffer);
      const storedName = `${Date.now()}_${sanitizeFileName(file.originalname)}`;
      const savedPath = path.join(UPLOADS_DIR, storedName);
      fs.writeFileSync(savedPath, file.buffer);
      savedItems.push({
        original_name: file.originalname,
        modality,
        saved_path: savedPath,
        media_url: `/uploads/${storedName}`,
        sha256,
        size_bytes: file.size,
      });
    }

    updateSession(caseId, {case_id: caseId, uploaded_files: savedItems});
    return res.json({status: 'success', case_id: caseId, files: savedItems});
  });

  app.post('/api/process/complete/:caseId', async (req, res) => {
    const {caseId} = req.params;
    const record = getSession(caseId);
    if (!record || !Array.isArray(record.uploaded_files) || record.uploaded_files.length === 0) {
      return res.status(404).json({status: 'error', error: `No uploaded files found for case '${caseId}'.`});
    }

    try {
      let imgRes: Record<string, any> | null = null;
      let audRes: Record<string, any> | null = null;
      let vidRes: Record<string, any> | null = null;

      for (const item of record.uploaded_files) {
        if (item.modality === 'image') {
          imgRes = await analyzeImageForensics(item.saved_path, item.original_name, item.sha256);
        } else if (item.modality === 'audio') {
          audRes = await analyzeAudioForensics(item.saved_path, item.original_name, item.sha256);
        } else if (item.modality === 'video') {
          vidRes = await analyzeVideoForensics(item.saved_path, item.original_name, item.sha256);
        }
      }

      const fused = fuseForensicSessions(imgRes, audRes, vidRes);
      const combined = {
        case_id: caseId,
        vision_results: imgRes,
        audio_results: audRes,
        video_results: vidRes,
        ...fused,
      };
      createSession(combined, caseId);
      return res.json({status: 'success', session_id: caseId, data: combined});
    } catch (err: any) {
      const code = err instanceof ForensicAnalysisError ? err.statusCode : 502;
      return res.status(code).json({status: 'error', error: err?.message || 'Case processing failed.'});
    }
  });

  app.post('/api/fuse', (req, res) => {
    const {image_session_id, audio_session_id, video_session_id} = req.body || {};
    const imgData = image_session_id ? getSession(image_session_id) : null;
    const audData = audio_session_id ? getSession(audio_session_id) : null;
    const vidData = video_session_id ? getSession(video_session_id) : null;

    if (!imgData && !audData && !vidData) {
      return res.status(400).json({
        status: 'error',
        error: 'Select at least one analyzed session (Image, Audio, or Video) to fuse.',
      });
    }

    const fused = fuseForensicSessions(imgData, audData, vidData);
    const sessionId = createSession(fused);
    fused.session_id = sessionId;
    return res.json({status: 'success', session_id: sessionId, data: fused});
  });

  app.post('/api/chat/:mode', async (req, res) => {
    const {mode} = req.params;
    const {session_id, question} = req.body || {};
    if (!session_id) {
      return res.status(400).json({status: 'error', error: "Missing 'session_id' in chat request."});
    }
    if (!question || !String(question).trim()) {
      return res.status(400).json({status: 'error', error: "Missing 'question' in chat request."});
    }
    const answer = await queryForensicChat(String(session_id), String(question), mode);
    return res.json({status: 'success', mode, answer});
  });

  app.get('/api/sessions', (_req, res) => {
    return res.json({status: 'success', sessions: listSessions()});
  });

  app.get('/api/results/:sessionId', (req, res) => {
    const data = getSession(req.params.sessionId);
    if (!data) {
      return res.status(404).json({status: 'error', error: `Session '${req.params.sessionId}' not found.`});
    }
    return res.json({status: 'success', session_id: req.params.sessionId, data});
  });

  app.get('/api/report/:sessionId', async (req, res) => {
    const data = getSession(req.params.sessionId);
    if (!data) {
      return res.status(404).json({status: 'error', error: `Session '${req.params.sessionId}' not found.`});
    }
    try {
      const pdfBuffer = await generateForensicPdfBuffer(req.params.sessionId, data);
      const shortId = req.params.sessionId.slice(0, 8);
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', `attachment; filename="CrimeVision_Forensic_Report_${shortId}.pdf"`);
      return res.send(pdfBuffer);
    } catch (err: any) {
      return res.status(500).json({status: 'error', error: err?.message || 'PDF report generation failed.'});
    }
  });

  // Multer error handler (e.g. file > 50 MB)
  app.use((err: any, _req: express.Request, res: express.Response, next: express.NextFunction) => {
    if (err instanceof multer.MulterError) {
      return res.status(400).json({status: 'error', error: `Upload error: ${err.message}`});
    }
    return next(err);
  });

  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: {middlewareMode: true},
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`CrimeVision AI server listening on http://localhost:${PORT}`);
  });
}

startServer();
