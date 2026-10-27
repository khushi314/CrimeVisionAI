import React, {useState} from 'react';
import {
  GitMerge,
  CheckCircle2,
  AlertTriangle,
  FileDown,
  Loader2,
  Clock,
  Play,
} from 'lucide-react';
import {
  AudioForensicResult,
  FusionForensicResult,
  ImageForensicResult,
  VideoForensicResult,
} from '../types/forensic';
import {
  analyzeSampleAsset,
  fuseSessions,
  getReportDownloadUrl,
} from '../services/api';
import {ForensicChatPanel} from './ForensicChatPanel';

interface MultimodalFusionViewProps {
  imageResult: ImageForensicResult | null;
  audioResult: AudioForensicResult | null;
  videoResult: VideoForensicResult | null;
  fusionResult: FusionForensicResult | null;
  onImageReady: (r: ImageForensicResult) => void;
  onAudioReady: (r: AudioForensicResult) => void;
  onVideoReady: (r: VideoForensicResult) => void;
  onFusionReady: (r: FusionForensicResult) => void;
}

export const MultimodalFusionView: React.FC<MultimodalFusionViewProps> = ({
  imageResult,
  audioResult,
  videoResult,
  fusionResult,
  onImageReady,
  onAudioReady,
  onVideoReady,
  onFusionReady,
}) => {
  const [useImage, setUseImage] = useState(true);
  const [useAudio, setUseAudio] = useState(true);
  const [useVideo, setUseVideo] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFuseActive = async () => {
    setError(null);
    setLoading(true);
    try {
      const fused = await fuseSessions({
        image_session_id: useImage && imageResult ? imageResult.session_id : undefined,
        audio_session_id: useAudio && audioResult ? audioResult.session_id : undefined,
        video_session_id: useVideo && videoResult ? videoResult.session_id : undefined,
      });
      onFusionReady(fused);
    } catch (err: any) {
      setError(err?.message || 'Multimodal fusion failed.');
    } finally {
      setLoading(false);
    }
  };

  const runPresetCase = async (preset: 'corroborated' | 'conflict') => {
    setError(null);
    setLoading(true);
    try {
      if (preset === 'corroborated') {
        const [img, aud, vid] = await Promise.all([
          analyzeSampleAsset<ImageForensicResult>('image', 'synthetic_retail_store_scene.jpg'),
          analyzeSampleAsset<AudioForensicResult>('audio', 'synthetic_witness_store_robbery.wav'),
          analyzeSampleAsset<VideoForensicResult>('video', 'synthetic_store_cctv.mp4'),
        ]);
        onImageReady(img);
        onAudioReady(aud);
        onVideoReady(vid);
        const fused = await fuseSessions({
          image_session_id: img.session_id,
          audio_session_id: aud.session_id,
          video_session_id: vid.session_id,
        });
        onFusionReady(fused);
      } else {
        // Cross-modal conflict preset: Office photograph vs Retail Store robbery witness audio
        const [img, aud] = await Promise.all([
          analyzeSampleAsset<ImageForensicResult>('image', 'synthetic_office_scene.jpg'),
          analyzeSampleAsset<AudioForensicResult>('audio', 'synthetic_witness_store_robbery.wav'),
        ]);
        onImageReady(img);
        onAudioReady(aud);
        const fused = await fuseSessions({
          image_session_id: img.session_id,
          audio_session_id: aud.session_id,
        });
        onFusionReady(fused);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed running multimodal benchmark preset.');
    } finally {
      setLoading(false);
    }
  };

  const hasAnyActive = Boolean(imageResult || audioResult || videoResult);

  return (
    <div className="space-y-6">
      {/* Fusion Orchestration Control */}
      <section className="rounded-lg border border-slate-800 bg-[#111827] p-5">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Cross-Modal Consistency Audit, Certainty Scoring &amp; Unified Timeline
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Corroborates spatial locations and physical objects across analyzed Image, Audio, and Video sessions, flags cross-modal conflicts, and assigns algorithmic certainty markers.
            </p>
          </div>

          <button
            type="button"
            disabled={loading || !hasAnyActive}
            onClick={handleFuseActive}
            className="inline-flex items-center justify-center gap-2 rounded bg-sky-500 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-45"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <GitMerge className="h-4 w-4" />}
            <span>Fuse Selected Sessions</span>
          </button>
        </div>

        {/* Active Session Checkboxes */}
        <div className="mt-4 grid grid-cols-1 gap-3 border-t border-slate-800/80 pt-4 md:grid-cols-3">
          <label className="flex cursor-pointer items-start gap-2.5 rounded border border-slate-800 bg-slate-950/60 p-3">
            <input
              type="checkbox"
              checked={useImage && Boolean(imageResult)}
              disabled={!imageResult}
              onChange={(e) => setUseImage(e.target.checked)}
              className="mt-1 accent-sky-500"
            />
            <div className="text-xs">
              <div className="font-medium text-slate-200">Image Session</div>
              <div className="mt-0.5 font-mono text-slate-400">
                {imageResult
                  ? `${imageResult.location} · ${imageResult.counts.objects} items`
                  : 'Not yet analyzed'}
              </div>
            </div>
          </label>

          <label className="flex cursor-pointer items-start gap-2.5 rounded border border-slate-800 bg-slate-950/60 p-3">
            <input
              type="checkbox"
              checked={useAudio && Boolean(audioResult)}
              disabled={!audioResult}
              onChange={(e) => setUseAudio(e.target.checked)}
              className="mt-1 accent-sky-500"
            />
            <div className="text-xs">
              <div className="font-medium text-slate-200">Audio Statement Session</div>
              <div className="mt-0.5 font-mono text-slate-400">
                {audioResult
                  ? `${audioResult.event_type} · ${audioResult.location}`
                  : 'Not yet analyzed'}
              </div>
            </div>
          </label>

          <label className="flex cursor-pointer items-start gap-2.5 rounded border border-slate-800 bg-slate-950/60 p-3">
            <input
              type="checkbox"
              checked={useVideo && Boolean(videoResult)}
              disabled={!videoResult}
              onChange={(e) => setUseVideo(e.target.checked)}
              className="mt-1 accent-sky-500"
            />
            <div className="text-xs">
              <div className="font-medium text-slate-200">Video CCTV Session</div>
              <div className="mt-0.5 font-mono text-slate-400">
                {videoResult
                  ? `${videoResult.scene_intelligence.location} · ${videoResult.duration_seconds}s`
                  : 'Not yet analyzed'}
              </div>
            </div>
          </label>
        </div>

        {/* One-Click End-to-End Multimodal Presets */}
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-800/80 pt-3.5">
          <span className="text-xs font-medium text-slate-400">Automated Multimodal Benchmarks:</span>
          <button
            type="button"
            disabled={loading}
            onClick={() => runPresetCase('corroborated')}
            className="inline-flex items-center gap-1.5 rounded border border-slate-700/80 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-emerald-500/50 hover:text-emerald-300 disabled:opacity-50"
          >
            <Play className="h-3 w-3 text-emerald-400" />
            Run Corroborated Store Robbery Case (Image + Audio + Video)
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => runPresetCase('conflict')}
            className="inline-flex items-center gap-1.5 rounded border border-slate-700/80 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-amber-500/50 hover:text-amber-300 disabled:opacity-50"
          >
            <Play className="h-3 w-3 text-amber-400" />
            Run Location Discrepancy Audit (Office Photo vs Store Audio)
          </button>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded border border-red-500/40 bg-red-950/30 px-3.5 py-2.5 text-sm text-red-200">
            <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}
      </section>

      {fusionResult && (
        <>
          {/* Consistency Audit Summary */}
          <section className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 lg:col-span-4">
              <div className="text-xs text-slate-400">Cross-Modal Consistency Score</div>
              <div
                className={`mt-1 font-mono text-3xl font-semibold tabular-nums ${
                  fusionResult.consistency.conflicts.length > 0
                    ? 'text-amber-400'
                    : 'text-emerald-400'
                }`}
              >
                {(fusionResult.consistency.overall_score * 100).toFixed(0)}%
              </div>
              <div className="mt-2 text-xs text-slate-400">
                Modalities Fused ·{' '}
                <span className="font-mono text-slate-200 uppercase">
                  {fusionResult.modalities_fused.join(' + ')}
                </span>
              </div>

              <div className="mt-4 border-t border-slate-800/80 pt-4">
                <a
                  href={getReportDownloadUrl(fusionResult.session_id)}
                  className="inline-flex items-center gap-1.5 rounded border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-sky-500/50 hover:text-sky-300"
                >
                  <FileDown className="h-3.5 w-3.5 text-sky-400" />
                  Export Unified PDF Report
                </a>
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 lg:col-span-8">
              <h3 className="border-b border-slate-800/80 pb-2.5 text-sm font-semibold text-slate-100">
                Corroborated Evidence Matches &amp; Discrepancy Flags
              </h3>

              <div className="mt-3 space-y-2.5">
                {fusionResult.consistency.matches.map((m, idx) => (
                  <div
                    key={`m_${idx}`}
                    className="flex items-start gap-2.5 rounded border border-emerald-500/25 bg-emerald-950/15 px-3.5 py-2.5 text-sm text-emerald-100"
                  >
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                    <span>{m}</span>
                  </div>
                ))}

                {fusionResult.consistency.conflicts.map((c, idx) => (
                  <div
                    key={`c_${idx}`}
                    className="flex items-start gap-2.5 rounded border border-red-500/35 bg-red-950/20 px-3.5 py-2.5 text-sm text-red-100"
                  >
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                    <span>{c}</span>
                  </div>
                ))}

                {fusionResult.consistency.matches.length === 0 &&
                  fusionResult.consistency.conflicts.length === 0 && (
                    <p className="text-sm text-slate-400">
                      Single-modality session baseline; fuse at least two distinct modalities (e.g. Image + Audio) to audit cross-modal consistency.
                    </p>
                  )}
              </div>
            </div>
          </section>

          {/* Unified Chronological Timeline with Certainty & Temporal Markers */}
          <section className="rounded-lg border border-slate-800 bg-[#111827] p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-sky-400" />
                <h3 className="text-sm font-semibold text-slate-100">
                  Unified Multimodal Timeline &amp; Certainty Audit
                </h3>
              </div>
              <span className="font-mono text-xs text-slate-400 tabular-nums">
                {fusionResult.unified_timeline.length} aligned events
              </span>
            </div>

            <div className="mt-3 divide-y divide-slate-800/80">
              {fusionResult.unified_timeline.map((ev, idx) => {
                const certColor =
                  ev.certainty === 'high'
                    ? 'text-emerald-400'
                    : ev.certainty === 'medium'
                    ? 'text-amber-400'
                    : 'text-red-400';
                return (
                  <div
                    key={idx}
                    className="flex flex-col justify-between gap-2 py-3 sm:flex-row sm:items-center"
                  >
                    <div className="flex items-start gap-3">
                      <span className="w-24 shrink-0 font-mono text-xs font-semibold text-sky-400 tabular-nums">
                        {ev.time}
                      </span>
                      <div>
                        <div className="text-sm text-slate-100">{ev.event}</div>
                        <div className="mt-0.5 font-mono text-[11px] text-slate-400 uppercase tabular-nums">
                          Source: {ev.modality} · Temporal: {ev.temporal_uncertainty}
                        </div>
                      </div>
                    </div>

                    <div className="shrink-0 font-mono text-xs tabular-nums">
                      <span className={`font-semibold uppercase ${certColor}`}>
                        {ev.certainty} certainty
                      </span>
                      {ev.confidence !== undefined && (
                        <span className="text-slate-500"> · {(ev.confidence * 100).toFixed(0)}%</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Fused Multimodal Hypotheses */}
          <section className="rounded-lg border border-slate-800 bg-[#111827] p-5">
            <h3 className="border-b border-slate-800/80 pb-2.5 text-sm font-semibold text-slate-100">
              Fused Investigative Hypotheses
            </h3>
            <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
              {fusionResult.scenarios.map((s, idx) => (
                <div
                  key={idx}
                  className="rounded border border-slate-800 bg-slate-950/60 p-4 text-sm leading-relaxed text-slate-200"
                >
                  {typeof s === 'string' ? (
                    s
                  ) : (
                    <>
                      <div className="font-mono text-xs font-semibold text-sky-400">{s.title}</div>
                      <p className="mt-1.5 text-slate-300">{s.description}</p>
                    </>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Grounded Fusion Chat */}
          <ForensicChatPanel
            mode="fusion"
            sessionId={fusionResult.session_id}
            suggestions={[
              'What happened at 00:05 across the fused timeline?',
              'Summarize any corroborations or conflicts between vision and audio.',
              'What are the three fused investigative hypotheses?',
            ]}
          />
        </>
      )}
    </div>
  );
};
