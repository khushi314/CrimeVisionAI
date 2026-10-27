import React, {useEffect, useState} from 'react';
import {
  Camera,
  Mic,
  Video,
  GitMerge,
  History,
  FileDown,
  ShieldCheck,
  X,
} from 'lucide-react';
import {
  AudioForensicResult,
  FusionForensicResult,
  ImageForensicResult,
  ModalityTab,
  SamplesCatalog,
  SessionHistoryItem,
  VideoForensicResult,
} from './types/forensic';
import {
  fetchRecentSessions,
  fetchSamplesCatalog,
  getReportDownloadUrl,
} from './services/api';
import {ImageAnalysisView} from './components/ImageAnalysisView';
import {AudioAnalysisView} from './components/AudioAnalysisView';
import {VideoAnalysisView} from './components/VideoAnalysisView';
import {MultimodalFusionView} from './components/MultimodalFusionView';

const NAV_TABS: Array<{id: ModalityTab; label: string; icon: React.ComponentType<{className?: string}>}> = [
  {id: 'image', label: 'Image Forensics', icon: Camera},
  {id: 'audio', label: 'Audio Intelligence', icon: Mic},
  {id: 'video', label: 'Video Surveillance', icon: Video},
  {id: 'fusion', label: 'Multimodal Fusion', icon: GitMerge},
];

export default function App() {
  const [activeTab, setActiveTab] = useState<ModalityTab>('image');
  const [samples, setSamples] = useState<SamplesCatalog>({image: [], audio: [], video: []});
  const [historyOpen, setHistoryOpen] = useState(false);
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);

  const [imageResult, setImageResult] = useState<ImageForensicResult | null>(null);
  const [audioResult, setAudioResult] = useState<AudioForensicResult | null>(null);
  const [videoResult, setVideoResult] = useState<VideoForensicResult | null>(null);
  const [fusionResult, setFusionResult] = useState<FusionForensicResult | null>(null);

  const refreshHistory = () => {
    fetchRecentSessions()
      .then(setSessions)
      .catch(() => {});
  };

  useEffect(() => {
    fetchSamplesCatalog()
      .then((cat) => {
        setSamples(cat);
      })
      .catch(() => {});
    refreshHistory();
  }, []);

  const loadStoredSession = async (item: SessionHistoryItem) => {
    try {
      const res = await fetch(`/api/results/${encodeURIComponent(item.session_id)}`);
      const json = await res.json();
      if (!res.ok || !json.data) return;
      const data = {...json.data, session_id: item.session_id};
      if (data.mode === 'image') {
        setImageResult(data);
        setActiveTab('image');
      } else if (data.mode === 'audio') {
        setAudioResult(data);
        setActiveTab('audio');
      } else if (data.mode === 'video') {
        setVideoResult(data);
        setActiveTab('video');
      } else if (data.mode === 'fusion') {
        setFusionResult(data);
        setActiveTab('fusion');
      }
      setHistoryOpen(false);
    } catch {
      // ignore
    }
  };

  const currentSessionId =
    activeTab === 'image'
      ? imageResult?.session_id
      : activeTab === 'audio'
      ? audioResult?.session_id
      : activeTab === 'video'
      ? videoResult?.session_id
      : fusionResult?.session_id;

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-100">
      {/* 3-Zone Top Bar (56px height contract) */}
      <header className="sticky top-0 z-30 border-b border-slate-800/90 bg-[#0b0f17]/95 backdrop-blur-md">
        <div className="mx-auto flex min-h-14 max-w-[1440px] flex-wrap items-center justify-between gap-3 px-4 py-2 sm:px-6">
          {/* Left Zone: Brand Identity */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded border border-sky-500/40 bg-sky-500/10 text-sky-400">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-tight text-white">CrimeVision AI</div>
              <div className="text-[11px] text-slate-400">
                Multimodal Forensic Analysis Platform
              </div>
            </div>
          </div>

          {/* Center Zone: Modality Switcher */}
          <nav
            aria-label="Forensic modality navigation"
            className="flex flex-wrap items-center gap-1 rounded border border-slate-800 bg-[#111827] p-1"
          >
            {NAV_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition ${
                    isActive
                      ? 'bg-sky-500 text-slate-950'
                      : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Zone: Active Report Export + Session History Drawer */}
          <div className="flex items-center gap-2">
            {currentSessionId && (
              <a
                href={getReportDownloadUrl(currentSessionId)}
                className="inline-flex items-center gap-1.5 rounded border border-slate-700 bg-[#111827] px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:border-sky-500/50 hover:text-sky-300"
              >
                <FileDown className="h-3.5 w-3.5 text-sky-400" />
                <span className="hidden sm:inline">Export PDF</span>
              </a>
            )}
            <button
              type="button"
              onClick={() => {
                refreshHistory();
                setHistoryOpen(true);
              }}
              className="inline-flex items-center gap-1.5 rounded border border-slate-700 bg-[#111827] px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:border-slate-600 hover:text-white"
            >
              <History className="h-3.5 w-3.5 text-slate-400" />
              <span>Sessions ({sessions.length})</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Forensic Workspace */}
      <main className="mx-auto max-w-[1440px] px-4 py-6 sm:px-6">
        {activeTab === 'image' && (
          <ImageAnalysisView
            samples={samples.image}
            result={imageResult}
            onResultChange={(res) => {
              setImageResult(res);
              if (res) {
                refreshHistory();
              }
            }}
          />
        )}

        {activeTab === 'audio' && (
          <AudioAnalysisView
            samples={samples.audio}
            result={audioResult}
            onResultReady={(res) => {
              setAudioResult(res);
              refreshHistory();
            }}
          />
        )}

        {activeTab === 'video' && (
          <VideoAnalysisView
            samples={samples.video}
            result={videoResult}
            onResultReady={(res) => {
              setVideoResult(res);
              refreshHistory();
            }}
          />
        )}

        {activeTab === 'fusion' && (
          <MultimodalFusionView
            imageResult={imageResult}
            audioResult={audioResult}
            videoResult={videoResult}
            fusionResult={fusionResult}
            onImageReady={setImageResult}
            onAudioReady={setAudioResult}
            onVideoReady={setVideoResult}
            onFusionReady={(res) => {
              setFusionResult(res);
              refreshHistory();
            }}
          />
        )}
      </main>

      {/* Responsible Forensic AI Footer */}
      <footer className="mt-10 border-t border-slate-900 py-5">
        <div className="mx-auto flex max-w-[1440px] flex-col justify-between gap-2 px-4 text-xs text-slate-500 sm:flex-row sm:px-6">
          <span>
            CrimeVision AI Capstone · Evidence-Grounded Multimodal Forensic Assistance
          </span>
          <span>
            Outputs represent algorithmic scene observations &amp; hypotheses; human verification is mandatory.
          </span>
        </div>
      </footer>

      {/* Persisted Session History Drawer */}
      {historyOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs">
          <div className="flex h-full w-full max-w-md flex-col border-l border-slate-800 bg-[#111827] p-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-semibold text-white">Persisted Forensic Sessions</h2>
                <p className="text-xs text-slate-400">Stored in data/sessions/session_&lt;uuid&gt;.json</p>
              </div>
              <button
                type="button"
                onClick={() => setHistoryOpen(false)}
                className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-3 flex-1 divide-y divide-slate-800/80 overflow-y-auto">
              {sessions.length === 0 ? (
                <p className="py-6 text-center text-xs text-slate-400">
                  No persisted sessions yet. Run an analysis to record a session.
                </p>
              ) : (
                sessions.map((s) => (
                  <button
                    key={s.session_id}
                    type="button"
                    onClick={() => loadStoredSession(s)}
                    className="flex w-full items-center justify-between py-3 text-left transition hover:bg-slate-900/50"
                  >
                    <div>
                      <div className="font-mono text-xs font-medium text-sky-400 uppercase tabular-nums">
                        {s.mode} · {s.session_id.slice(0, 8)}
                      </div>
                      <div className="mt-0.5 text-xs text-slate-200">
                        {s.file_name || s.location || 'Forensic Case Record'}
                      </div>
                    </div>
                    <span className="font-mono text-[11px] text-slate-500 tabular-nums">
                      {s.created_at_utc ? s.created_at_utc.slice(11, 19) : 'Saved'}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
