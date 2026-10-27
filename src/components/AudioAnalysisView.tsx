import React, {useRef, useState} from 'react';
import {
  Upload,
  Volume2,
  FileDown,
  Loader2,
  AlertTriangle,
  Clock,
  Globe,
} from 'lucide-react';
import {AudioForensicResult, SampleAssetItem} from '../types/forensic';
import {
  analyzeUploadedFile,
  analyzeSampleAsset,
  getReportDownloadUrl,
} from '../services/api';
import {ForensicChatPanel} from './ForensicChatPanel';

interface AudioAnalysisViewProps {
  samples: SampleAssetItem[];
  result: AudioForensicResult | null;
  onResultReady: (res: AudioForensicResult) => void;
}

type LangKey = 'english' | 'hindi' | 'telugu' | 'french';

const LANGUAGE_LABELS: Array<{key: LangKey; label: string}> = [
  {key: 'english', label: 'English'},
  {key: 'hindi', label: 'Hindi (हिन्दी)'},
  {key: 'telugu', label: 'Telugu (తెలుగు)'},
  {key: 'french', label: 'French (Français)'},
];

export const AudioAnalysisView: React.FC<AudioAnalysisViewProps> = ({
  samples,
  result,
  onResultReady,
}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeLang, setActiveLang] = useState<LangKey>('english');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setLoading(true);
    try {
      const analyzed = await analyzeUploadedFile<AudioForensicResult>('/api/analyze-audio', file);
      onResultReady(analyzed);
    } catch (err: any) {
      setError(err?.message || 'Audio statement analysis failed.');
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  const handleLoadSample = async (filename: string) => {
    setError(null);
    setLoading(true);
    try {
      const analyzed = await analyzeSampleAsset<AudioForensicResult>('audio', filename);
      onResultReady(analyzed);
    } catch (err: any) {
      setError(err?.message || 'Failed to analyze sample witness audio.');
    } finally {
      setLoading(false);
    }
  };

  const seekAudio = (seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = seconds;
      audioRef.current.play().catch(() => {});
    }
  };

  return (
    <div className="space-y-6">
      {/* Intake & Sample Bar */}
      <section className="rounded-lg border border-slate-800 bg-[#111827] p-5">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Witness Audio Transcription, Multilingual Translation &amp; Event Timeline
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Processes recorded statements (.wav, .mp3, .m4a, .ogg, .flac), extracts incident intelligence, translates into English, Hindi, Telugu &amp; French, and aligns timestamped events.
            </p>
          </div>
          <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded bg-sky-500 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-400">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            <span>{loading ? 'Transcribing Audio...' : 'Upload Audio Statement'}</span>
            <input
              type="file"
              accept=".wav,.mp3,.m4a,.ogg,.flac"
              onChange={handleFileChange}
              disabled={loading}
              className="hidden"
            />
          </label>
        </div>

        {samples.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-800/80 pt-3.5">
            <span className="text-xs font-medium text-slate-400">Synthetic Witness Recordings:</span>
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
          {/* Audio Player + Key Intelligence Strip */}
          <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-5">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Volume2 className="h-4 w-4 text-sky-400" />
                <span>Source Audio Playback · {result.duration_seconds}s</span>
              </div>
              {result.media_url && (
                <audio
                  ref={audioRef}
                  controls
                  src={result.media_url}
                  className="mt-3 w-full"
                />
              )}
              <div className="mt-3 font-mono text-xs text-slate-400 tabular-nums">
                {result.file_name || 'statement.wav'}
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-[#111827] p-5">
              <div className="text-xs text-slate-400">Classified Incident Type</div>
              <div className="mt-1 font-mono text-xl font-semibold text-amber-400">
                {result.event_type}
              </div>
              <div className="mt-2 text-xs text-slate-400">
                Reported Location · <span className="font-medium text-slate-200">{result.location}</span>
              </div>
            </div>

            <div className="flex flex-col justify-between rounded-lg border border-slate-800 bg-[#111827] p-5">
              <div>
                <div className="text-xs text-slate-400">Subject &amp; Witness Entities</div>
                <div className="mt-1 text-sm text-slate-200">
                  {result.facts.who.join(' · ')}
                </div>
                <div className="mt-1.5 text-xs text-slate-400">
                  Description: {result.facts.suspect_description}
                </div>
              </div>
              <div className="mt-3">
                <a
                  href={getReportDownloadUrl(result.session_id)}
                  className="inline-flex items-center gap-1.5 rounded border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-sky-500/50 hover:text-sky-300"
                >
                  <FileDown className="h-3.5 w-3.5 text-sky-400" />
                  Download PDF Report
                </a>
              </div>
            </div>
          </section>

          {/* Intelligence Report + 4-Language Translations */}
          <section className="grid grid-cols-1 gap-6 lg:grid-cols-5">
            <div className="space-y-6 lg:col-span-3">
              {/* Executive Intelligence Summary */}
              <div className="rounded-lg border border-slate-800 bg-[#111827] p-5">
                <h3 className="border-b border-slate-800/80 pb-2.5 text-sm font-semibold text-slate-100">
                  Audio Intelligence Summary
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-200">
                  {result.ai_summary}
                </p>
                {result.sha256 && (
                  <div className="mt-4 border-t border-slate-800/80 pt-2.5 font-mono text-[11px] text-slate-500 tabular-nums">
                    SHA-256 Digest: {result.sha256}
                  </div>
                )}
              </div>

              {/* Multilingual Transcripts & Translations */}
              <div className="rounded-lg border border-slate-800 bg-[#111827] p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4 text-sky-400" />
                    <h3 className="text-sm font-semibold text-slate-100">
                      Transcripts &amp; Multilingual Translations
                    </h3>
                  </div>

                  <div className="flex flex-wrap gap-1 rounded border border-slate-800 bg-slate-950 p-1">
                    {LANGUAGE_LABELS.map((item) => (
                      <button
                        key={item.key}
                        type="button"
                        onClick={() => setActiveLang(item.key)}
                        className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                          activeLang === item.key
                            ? 'bg-sky-500 text-slate-950'
                            : 'text-slate-300 hover:text-white'
                        }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-4 rounded border border-slate-800/90 bg-slate-950/60 p-4 text-sm leading-relaxed text-slate-100">
                  {result.translations[activeLang]}
                </div>
              </div>
            </div>

            {/* Timestamped Crime Event Timeline */}
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 lg:col-span-2">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-400" />
                  <h3 className="text-sm font-semibold text-slate-100">
                    Statement Event Timeline
                  </h3>
                </div>
                <span className="text-xs text-slate-400">Click row to seek audio</span>
              </div>

              <div className="mt-3 divide-y divide-slate-800/80">
                {result.timeline.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => seekAudio(item.seconds)}
                    className="flex w-full items-start gap-3 py-3 text-left transition hover:bg-slate-900/50"
                  >
                    <span className="mt-0.5 shrink-0 font-mono text-xs font-semibold text-sky-400 tabular-nums">
                      {item.time}
                    </span>
                    <span className="text-sm leading-snug text-slate-200">{item.event}</span>
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Grounded Audio Q&A */}
          <ForensicChatPanel
            mode="audio"
            sessionId={result.session_id}
            suggestions={[
              'Summarize what the witness reported.',
              'What was described at 00:05?',
              'Where did the incident take place?',
              'What happened at 00:12?',
            ]}
          />
        </>
      )}
    </div>
  );
};
