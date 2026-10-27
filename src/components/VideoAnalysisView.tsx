import React, {useRef, useState} from 'react';
import {
  Upload,
  Video,
  FileDown,
  Loader2,
  AlertTriangle,
  Clock,
  ShieldAlert,
  CheckCircle2,
} from 'lucide-react';
import {SampleAssetItem, VideoForensicResult} from '../types/forensic';
import {
  analyzeUploadedFile,
  analyzeSampleAsset,
  getReportDownloadUrl,
} from '../services/api';
import {ForensicChatPanel} from './ForensicChatPanel';

interface VideoAnalysisViewProps {
  samples: SampleAssetItem[];
  result: VideoForensicResult | null;
  onResultReady: (res: VideoForensicResult) => void;
}

export const VideoAnalysisView: React.FC<VideoAnalysisViewProps> = ({
  samples,
  result,
  onResultReady,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setLoading(true);
    try {
      const analyzed = await analyzeUploadedFile<VideoForensicResult>('/api/analyze-video', file);
      onResultReady(analyzed);
    } catch (err: any) {
      setError(err?.message || 'Surveillance video analysis failed.');
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  const handleLoadSample = async (filename: string) => {
    setError(null);
    setLoading(true);
    try {
      const analyzed = await analyzeSampleAsset<VideoForensicResult>('video', filename);
      onResultReady(analyzed);
    } catch (err: any) {
      setError(err?.message || 'Failed to analyze sample CCTV clip.');
    } finally {
      setLoading(false);
    }
  };

  const seekVideo = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play().catch(() => {});
    }
  };

  const isNormal = result?.classification === 'NORMAL ACTIVITY';

  return (
    <div className="space-y-6">
      {/* Intake & Sample Bar */}
      <section className="rounded-lg border border-slate-800 bg-[#111827] p-5">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              1Hz Surveillance Video Decomposition &amp; Hash-Indexed Event Timeline
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Samples CCTV clips (.mp4, .webm, .mov, .avi) at 1 frame/second (max 30s), tracks person/weapon counts, classifies incident status, and builds a clickable second-by-second timeline.
            </p>
          </div>
          <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded bg-sky-500 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-400">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            <span>{loading ? 'Extracting 1Hz Frames...' : 'Upload CCTV Footage'}</span>
            <input
              type="file"
              accept=".mp4,.webm,.mov,.avi,.mkv"
              onChange={handleFileChange}
              disabled={loading}
              className="hidden"
            />
          </label>
        </div>

        {samples.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-800/80 pt-3.5">
            <span className="text-xs font-medium text-slate-400">Synthetic CCTV Footage:</span>
            {samples.map((s) => (
              <button
                key={s.id}
                type="button"
                disabled={loading}
                onClick={() => handleLoadSample(s.filename)}
                className="rounded border border-slate-700/80 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:border-sky-500/50 hover:text-sky-300 disabled:opacity-50"
              >
                {s.label}
              </button>
            ))}
          </div>
        )}

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded border border-red-500/40 bg-red-950/30 px-3.5 py-2.5 text-sm text-red-200">
            <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}
      </section>

      {result && (
        <>
          {/* Sequence Classification Banner */}
          <section
            className={`rounded-lg border p-5 ${
              isNormal
                ? 'border-emerald-500/35 bg-emerald-950/15'
                : 'border-amber-500/40 bg-amber-950/15'
            }`}
          >
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <div className="flex items-start gap-3">
                {isNormal ? (
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
                ) : (
                  <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />
                )}
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`font-mono text-sm font-semibold ${
                        isNormal ? 'text-emerald-300' : 'text-amber-300'
                      }`}
                    >
                      {result.classification}
                    </span>
                    <span className="font-mono text-xs text-slate-400 tabular-nums">
                      · Confidence {(result.classification_confidence * 100).toFixed(0)}% ·{' '}
                      {result.duration_seconds}s clip
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-200">
                    Reason: {result.classification_reason}
                  </p>
                </div>
              </div>

              <a
                href={getReportDownloadUrl(result.session_id)}
                className="inline-flex shrink-0 items-center gap-1.5 rounded border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-sky-500/50 hover:text-sky-300"
              >
                <FileDown className="h-3.5 w-3.5 text-sky-400" />
                Download PDF Report
              </a>
            </div>
          </section>

          {/* Video Player + Scene Intelligence + Event Timeline */}
          <section className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* Left 7 cols: Player + Scene Intelligence */}
            <div className="space-y-6 lg:col-span-7">
              <div className="rounded-lg border border-slate-800 bg-[#111827] p-4">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Video className="h-4 w-4 text-sky-400" />
                    <h3 className="text-sm font-semibold text-slate-100">
                      Surveillance Stream Playback
                    </h3>
                  </div>
                  <span className="font-mono text-xs text-slate-400 tabular-nums">
                    {result.frames_analyzed ?? Math.ceil(result.duration_seconds)} frames @ 1Hz
                  </span>
                </div>

                {result.media_url && (
                  <video
                    ref={videoRef}
                    controls
                    src={result.media_url}
                    className="aspect-video w-full rounded border border-slate-800 bg-slate-950"
                  />
                )}
              </div>

              {/* Scene Intelligence */}
              <div className="rounded-lg border border-slate-800 bg-[#111827] p-5">
                <h3 className="border-b border-slate-800/80 pb-2.5 text-sm font-semibold text-slate-100">
                  Scene Intelligence &amp; AI Visual Summary
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-200">
                  {result.visual_summary}
                </p>

                <div className="mt-4 grid grid-cols-2 gap-4 border-t border-slate-800/80 pt-4 sm:grid-cols-4">
                  <div>
                    <div className="text-xs text-slate-400">People Count</div>
                    <div className="mt-0.5 font-mono text-lg font-semibold text-sky-400 tabular-nums">
                      {result.scene_intelligence.people_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Weapons Count</div>
                    <div
                      className={`mt-0.5 font-mono text-lg font-semibold tabular-nums ${
                        result.scene_intelligence.weapons_count > 0 ? 'text-red-400' : 'text-emerald-400'
                      }`}
                    >
                      {result.scene_intelligence.weapons_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Location</div>
                    <div className="mt-0.5 text-sm font-medium text-slate-100 capitalize">
                      {result.scene_intelligence.location}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Action Pattern</div>
                    <div className="mt-0.5 text-sm font-medium text-slate-100 capitalize">
                      {result.scene_intelligence.action}
                    </div>
                  </div>
                </div>

                <div className="mt-3 text-xs text-slate-400">
                  Objects Detected:{' '}
                  <span className="text-slate-200">
                    {result.scene_intelligence.objects_detected.join(' · ') || 'None'}
                  </span>
                </div>
              </div>
            </div>

            {/* Right 5 cols: Clickable Second-by-Second Event Timeline */}
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 lg:col-span-5">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-400" />
                  <h3 className="text-sm font-semibold text-slate-100">
                    Second-by-Second Event Timeline
                  </h3>
                </div>
                <span className="text-xs text-slate-400">Click timestamp to seek</span>
              </div>

              <div className="mt-3 divide-y divide-slate-800/80">
                {result.timeline.map((item, idx) => {
                  const timeColor =
                    item.severity === 'alert'
                      ? 'text-red-400'
                      : item.severity === 'elevated'
                      ? 'text-amber-400'
                      : 'text-sky-400';
                  return (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => seekVideo(item.seconds)}
                      className="flex w-full items-start gap-3 py-3 text-left transition hover:bg-slate-900/60"
                    >
                      <span
                        className={`mt-0.5 w-24 shrink-0 font-mono text-xs font-semibold tabular-nums ${timeColor}`}
                      >
                        {item.time}
                      </span>
                      <div className="flex-1">
                        <div className="text-sm leading-snug text-slate-200">{item.event}</div>
                        {item.confidence !== undefined && (
                          <div className="mt-0.5 font-mono text-[11px] text-slate-500 tabular-nums">
                            Conf {(item.confidence * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Grounded Video Q&A with Regex O(1) Timestamp Lookup */}
          <ForensicChatPanel
            mode="video"
            sessionId={result.session_id}
            suggestions={[
              'What happened at 00:05?',
              'Describe activity at 00:02.',
              'How many people and objects were detected across the video?',
              'Why did the classifier assign this incident label?',
            ]}
          />
        </>
      )}
    </div>
  );
};
