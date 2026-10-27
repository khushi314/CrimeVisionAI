import React, {useEffect, useRef, useState} from 'react';
import {
  Upload,
  Eye,
  FileDown,
  Loader2,
  AlertTriangle,
  Layers,
  Crosshair,
  Info,
  RefreshCw,
  Image as ImageIcon,
} from 'lucide-react';
import {
  ImageForensicResult,
  Object3DNode,
  SampleAssetItem,
} from '../types/forensic';
import {
  analyzeUploadedFile,
  analyzeSampleAsset,
  getReportDownloadUrl,
} from '../services/api';
import {Scene3DReconstruction} from './Scene3DReconstruction';
import {ForensicChatPanel} from './ForensicChatPanel';

interface ImageAnalysisViewProps {
  samples: SampleAssetItem[];
  result: ImageForensicResult | null;
  onResultChange: (res: ImageForensicResult | null) => void;
}

type PendingSource =
  | {kind: 'upload'; file: File; previewUrl: string}
  | {kind: 'sample'; sample: SampleAssetItem};

export const ImageAnalysisView: React.FC<ImageAnalysisViewProps> = ({
  samples,
  result,
  onResultChange,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showOverlay, setShowOverlay] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [pendingSource, setPendingSource] = useState<PendingSource | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const blobUrlRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
      }
    };
  }, []);

  const runUploadAnalysis = async (file: File) => {
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
    }
    const previewUrl = URL.createObjectURL(file);
    blobUrlRef.current = previewUrl;

    // Immediately clear stale results from any previous image before starting inference
    onResultChange(null);
    setSelectedNodeId(null);
    setError(null);
    setPendingSource({kind: 'upload', file, previewUrl});
    setLoading(true);

    try {
      const analyzed = await analyzeUploadedFile<ImageForensicResult>('/api/analyze-image', file);
      onResultChange(analyzed);
    } catch (err: any) {
      setError(err?.message || 'Image forensic analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    await runUploadAnalysis(file);
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    if (loading) return;
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    await runUploadAnalysis(file);
  };

  const handleLoadSample = async (sample: SampleAssetItem) => {
    // Immediately clear stale results before analyzing selected reference image
    onResultChange(null);
    setSelectedNodeId(null);
    setError(null);
    setPendingSource({kind: 'sample', sample});
    setLoading(true);

    try {
      const analyzed = await analyzeSampleAsset<ImageForensicResult>('image', sample.filename);
      onResultChange(analyzed);
    } catch (err: any) {
      setError(err?.message || 'Failed to analyze reference image.');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async () => {
    if (!pendingSource || loading) return;
    if (pendingSource.kind === 'upload') {
      await runUploadAnalysis(pendingSource.file);
    } else {
      await handleLoadSample(pendingSource.sample);
    }
  };

  const isVlmMode =
    !result?.provenance || result.provenance.analysis_mode === 'multimodal_vision_vlm';

  // Map detection array index -> 3D marker ID (`ev_1`, `ev_2`, ...) for detections with valid boxes
  let bboxCounter = 0;
  const detectionMarkerIds = (result?.detections || []).map((det) => {
    if (det.normalized_bbox && det.normalized_bbox.length === 4) {
      bboxCounter += 1;
      return {markerId: `ev_${bboxCounter}`, markerNumber: bboxCounter};
    }
    return {markerId: null, markerNumber: null};
  });

  const activePreviewUrl =
    pendingSource?.kind === 'upload'
      ? pendingSource.previewUrl
      : pendingSource?.kind === 'sample'
      ? pendingSource.sample.url
      : null;

  const activePendingName =
    pendingSource?.kind === 'upload'
      ? pendingSource.file.name
      : pendingSource?.kind === 'sample'
      ? pendingSource.sample.filename
      : null;

  return (
    <div className="space-y-6">
      {/* Intake & Sample Bar */}
      <section className="rounded-lg border border-slate-800 bg-[#111827] p-5">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Multimodal Image Forensics &amp; Scene Inspection
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Uploads your actual image to a multimodal vision model to dynamically identify visible objects, people, potential weapons, environment context, and grounded investigative hypotheses.
            </p>
          </div>
          <label
            className={`inline-flex items-center justify-center gap-2 rounded bg-sky-500 px-4 py-2.5 text-sm font-medium text-slate-950 transition ${
              loading ? 'cursor-not-allowed opacity-60' : 'cursor-pointer hover:bg-sky-400'
            }`}
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            <span>{loading ? 'Analyzing Uploaded Image...' : 'Upload Evidence Photo'}</span>
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.webp,.bmp,.gif"
              onChange={handleFileChange}
              disabled={loading}
              className="hidden"
            />
          </label>
        </div>

        {samples.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-800/80 pt-3.5">
            <span className="text-xs font-medium text-slate-400">
              Optional Reference Test Images (Live Multimodal Analysis):
            </span>
            {samples.map((s) => (
              <button
                key={s.id}
                type="button"
                disabled={loading}
                onClick={() => handleLoadSample(s)}
                className="rounded border border-slate-700/80 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:border-sky-500/50 hover:text-sky-300 disabled:opacity-50"
              >
                {s.label}
              </button>
            ))}
          </div>
        )}

        {error && (
          <div className="mt-4 flex flex-col justify-between gap-3 rounded border border-red-500/40 bg-red-950/30 px-4 py-3 text-sm text-red-200 sm:flex-row sm:items-center">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
              <div>
                <div className="font-medium text-red-100">Image Analysis Error</div>
                <div className="mt-0.5 text-xs text-red-200/90">{error}</div>
              </div>
            </div>
            {pendingSource && (
              <button
                type="button"
                disabled={loading}
                onClick={handleRetry}
                className="inline-flex shrink-0 items-center gap-1.5 rounded border border-red-400/40 bg-red-950/60 px-3 py-1.5 text-xs font-medium text-red-100 transition hover:border-red-300 hover:bg-red-900/50 disabled:opacity-50"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Retry Analysis
              </button>
            )}
          </div>
        )}
      </section>

      {/* Live Loading State (Stale Results Cleared) */}
      {loading && (
        <section className="rounded-lg border border-sky-500/30 bg-[#111827] p-6">
          <div className="grid grid-cols-1 items-center gap-6 md:grid-cols-12">
            {activePreviewUrl && (
              <div className="flex h-56 items-center justify-center overflow-hidden rounded-lg border border-slate-800 bg-slate-950 p-2 md:col-span-5">
                <img
                  src={activePreviewUrl}
                  alt={activePendingName || 'Uploading preview'}
                  className="max-h-full max-w-full rounded object-contain opacity-90"
                />
              </div>
            )}
            <div className={activePreviewUrl ? 'md:col-span-7' : 'md:col-span-12'}>
              <div className="inline-flex items-center gap-2 rounded border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 font-mono text-xs text-sky-300">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>LIVE MULTIMODAL VISION INFERENCE</span>
              </div>
              <h3 className="mt-3 text-base font-semibold text-slate-100">
                Inspecting {activePendingName ? `"${activePendingName}"` : 'uploaded photograph'}...
              </h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-400">
                Previous scene findings have been cleared. Sending raw image bytes to the multimodal vision model to dynamically identify visible objects, people, potential weapons, spatial context, and grounded hypotheses.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Initial Empty / Dropzone State (No Preloaded Demo Results) */}
      {!loading && !result && (
        <section
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          className={`rounded-lg border border-dashed p-10 text-center transition ${
            dragActive
              ? 'border-sky-400 bg-sky-950/20'
              : 'border-slate-800 bg-[#111827]/70 hover:border-slate-700'
          }`}
        >
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-sky-400">
            <ImageIcon className="h-6 w-6" />
          </div>
          <h3 className="mt-4 text-sm font-semibold text-slate-100">
            No Image Analyzed Yet — Upload Any Photograph to Begin
          </h3>
          <p className="mx-auto mt-1.5 max-w-xl text-xs leading-relaxed text-slate-400">
            Drag and drop a JPG, PNG, WebP, BMP, or GIF image here, or click <strong className="text-slate-200">Upload Evidence Photo</strong> above. Every detection, scene classification, and observation is generated dynamically from the actual image you upload.
          </p>
          {error && activePreviewUrl && (
            <div className="mx-auto mt-5 max-w-xs overflow-hidden rounded border border-slate-800 bg-slate-950 p-2">
              <img
                src={activePreviewUrl}
                alt={activePendingName || 'Selected image'}
                className="mx-auto max-h-40 object-contain"
              />
              <div className="mt-1.5 truncate font-mono text-[11px] text-slate-400">
                {activePendingName}
              </div>
            </div>
          )}
        </section>
      )}

      {!loading && result && (
        <>
          {/* Provenance & Simulation Transparency Notice */}
          {isVlmMode && (
            <section className="flex items-start gap-2.5 rounded-lg border border-amber-500/30 bg-amber-950/20 px-4 py-3 text-xs text-amber-100/90">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
              <div>
                <span className="font-semibold text-amber-200">
                  Multimodal Vision Analysis ({result.provenance?.model || 'Gemini Multimodal VLM'}):
                </span>{' '}
                {result.provenance?.disclaimer ||
                  'All scene findings and object identifications are derived dynamically from the uploaded image. Bounding boxes, visibility percentages, and 3D floor-plane coordinates are VLM-estimated / simulated rather than produced by a calibrated pixel-level object detector.'}
              </div>
            </section>
          )}

          {/* KPI Summary Strip */}
          <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-4">
              <div className="text-xs text-slate-400">Visible Items Flagged</div>
              <div className="mt-1 font-mono text-2xl font-semibold text-slate-100 tabular-nums">
                {result.counts.objects}
              </div>
              <div className="mt-1 text-xs text-slate-400">
                {result.file_name ? `Source: ${result.file_name}` : 'Foreground items in frame'}
              </div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-4">
              <div className="text-xs text-slate-400">Humans Observed</div>
              <div className="mt-1 font-mono text-2xl font-semibold text-sky-400 tabular-nums">
                {result.counts.persons}
              </div>
              <div className="mt-1 text-xs text-slate-400">
                {result.counts.persons > 0 ? 'Objective visual presence' : 'No people visible in image'}
              </div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-4">
              <div className="text-xs text-slate-400">Potential Weapons</div>
              <div
                className={`mt-1 font-mono text-2xl font-semibold tabular-nums ${
                  result.counts.weapons > 0 ? 'text-red-400' : 'text-emerald-400'
                }`}
              >
                {result.counts.weapons}
              </div>
              <div className="mt-1 text-xs text-slate-400">
                {result.counts.weapons > 0 ? 'Requires priority chain-of-custody' : 'None visible in image'}
              </div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-4">
              <div className="text-xs text-slate-400">Observed Environment</div>
              <div className="mt-1 text-lg font-semibold text-slate-100 capitalize">
                {result.location}
              </div>
              <div className="mt-1 font-mono text-xs text-slate-400 tabular-nums">
                {result.location_confidence !== null
                  ? `Est. Clarity ${(result.location_confidence * 100).toFixed(0)}% (VLM)`
                  : 'Clarity Score Unavailable'}
              </div>
            </div>
          </section>

          {/* Dual Spatial Viewports: 2D Annotated Photo + Simulated Three.js 3D Projection */}
          <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            {/* 2D Annotated Frame */}
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Crosshair className="h-4 w-4 text-sky-400" />
                  <div>
                    <h3 className="text-sm font-semibold text-slate-100">
                      Uploaded Image &amp; Visual Localization
                    </h3>
                    <div className="font-mono text-[11px] text-amber-300/90">
                      {isVlmMode
                        ? 'Boxes & scores: VLM-Estimated (Approximate)'
                        : 'Calibrated Object Detector Output'}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowOverlay((v) => !v)}
                  className="inline-flex items-center gap-1.5 rounded border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-300 hover:border-sky-500/40 hover:text-white"
                >
                  <Eye className="h-3.5 w-3.5 text-sky-400" />
                  {showOverlay ? 'Hide Regions' : 'Show Regions'}
                </button>
              </div>

              <div className="flex h-[420px] w-full items-center justify-center overflow-hidden rounded-lg border border-slate-800 bg-slate-950 p-2">
                {result.media_url && (
                  <div className="relative inline-flex max-h-full max-w-full items-center justify-center">
                    <img
                      src={result.media_url}
                      alt={result.file_name || 'Analyzed scene'}
                      className="block max-h-[400px] w-auto max-w-full select-none object-contain"
                    />
                    {showOverlay && (
                      <svg
                        viewBox="0 0 1000 1000"
                        preserveAspectRatio="none"
                        className="absolute inset-0 h-full w-full"
                      >
                        {result.detections.map((det, idx) => {
                          if (!det.normalized_bbox || det.normalized_bbox.length !== 4) {
                            return null;
                          }
                          const [nx1, ny1, nx2, ny2] = det.normalized_bbox;
                          const x = nx1 * 1000;
                          const y = ny1 * 1000;
                          const w = Math.max(20, (nx2 - nx1) * 1000);
                          const h = Math.max(20, (ny2 - ny1) * 1000);
                          const markerMeta = detectionMarkerIds[idx];
                          const nodeId = markerMeta.markerId || `det_${idx + 1}`;
                          const badgeNum = markerMeta.markerNumber ?? idx + 1;
                          const isSel = selectedNodeId === nodeId;
                          const stroke =
                            det.category === 'weapon'
                              ? '#ef4444'
                              : det.category === 'person'
                              ? '#38bdf8'
                              : '#facc15';
                          const confLabel =
                            det.confidence !== null
                              ? `${det.confidence_simulated ? '~' : ''}${(det.confidence * 100).toFixed(0)}%`
                              : 'N/A';
                          const labelStr = `#${badgeNum} ${det.label} (${confLabel})`;
                          return (
                            <g
                              key={nodeId}
                              onClick={() => setSelectedNodeId(isSel ? null : nodeId)}
                              className="cursor-pointer"
                            >
                              <rect
                                x={x}
                                y={y}
                                width={w}
                                height={h}
                                fill={isSel ? 'rgba(56,189,248,0.16)' : 'transparent'}
                                stroke={stroke}
                                strokeWidth={isSel ? 5 : 3}
                                strokeDasharray={det.bbox_simulated ? '10 5' : undefined}
                              />
                              <rect
                                x={Math.min(x, 660)}
                                y={Math.max(0, y - 34)}
                                width={Math.min(340, Math.max(150, labelStr.length * 13 + 24))}
                                height={32}
                                fill="#0f172ae6"
                              />
                              <text
                                x={Math.min(x, 660) + 10}
                                y={Math.max(22, y - 12)}
                                fill={stroke}
                                fontSize="20"
                                fontFamily="IBM Plex Mono, monospace"
                                fontWeight="600"
                              >
                                {labelStr}
                              </text>
                            </g>
                          );
                        })}
                      </svg>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* 3D Three.js Reconstruction */}
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-amber-400" />
                  <div>
                    <h3 className="text-sm font-semibold text-slate-100">
                      Simulated 3D Scene Layout (Three.js)
                    </h3>
                    <div className="font-mono text-[11px] text-amber-300/90">
                      Heuristic 2D→3D Floor-Plane Approximation
                    </div>
                  </div>
                </div>
                <span className="font-mono text-xs text-slate-400">
                  Drag to orbit · Click marker to inspect
                </span>
              </div>

              <Scene3DReconstruction
                scene3d={result.scene_3d}
                selectedId={selectedNodeId}
                onSelectNode={(node: Object3DNode | null) =>
                  setSelectedNodeId(node ? node.id : null)
                }
              />
            </div>
          </section>

          {/* AI Scene Summary + Cataloged Facts */}
          <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 lg:col-span-2">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div>
                  <div className="text-xs font-medium text-sky-400">
                    {result.ai_scene_summary.summary_type}
                  </div>
                  <h3 className="mt-0.5 text-sm font-semibold text-slate-100">
                    Dynamic Visual Scene Findings
                  </h3>
                </div>
                <a
                  href={getReportDownloadUrl(result.session_id)}
                  className="inline-flex items-center gap-1.5 rounded border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:border-sky-500/50 hover:text-sky-300"
                >
                  <FileDown className="h-3.5 w-3.5 text-sky-400" />
                  Download PDF Report
                </a>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-slate-200">
                {result.ai_scene_summary.brief_description}
              </p>
              {result.visual_summary &&
                result.visual_summary !== result.ai_scene_summary.brief_description && (
                  <p className="mt-2.5 text-xs leading-relaxed text-slate-400">
                    {result.visual_summary}
                  </p>
                )}

              <div className="mt-4 grid grid-cols-1 gap-4 border-t border-slate-800/80 pt-4 sm:grid-cols-2">
                <div>
                  <div className="text-xs font-medium text-slate-400">
                    Observed Postures, States &amp; Scene Conditions
                  </div>
                  <p className="mt-1 text-sm text-slate-200">
                    {result.actions_detected.join(' · ') || 'None observed'}
                  </p>
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-400">Visible Scene Items &amp; Notes</div>
                  <p className="mt-1 text-sm text-slate-200">
                    {result.evidence_facts.length > 0
                      ? result.evidence_facts.join(' · ')
                      : 'No distinct foreground items flagged'}
                  </p>
                </div>
              </div>
              {result.sha256 && (
                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/80 pt-3 font-mono text-[11px] text-slate-500 tabular-nums">
                  <span>SHA-256 Digest: {result.sha256}</span>
                  {result.provenance?.image_dimensions && (
                    <span>
                      Dimensions: {result.provenance.image_dimensions.width}×
                      {result.provenance.image_dimensions.height}px
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Detection Table */}
            <div className="rounded-lg border border-slate-800 bg-[#111827] p-5">
              <div className="border-b border-slate-800/80 pb-3">
                <h3 className="text-sm font-semibold text-slate-100">
                  Detected Items &amp; Region Log
                </h3>
                <p className="mt-0.5 font-mono text-[11px] text-slate-400">
                  {isVlmMode
                    ? 'VLM-estimated regions & visibility scores'
                    : 'Calibrated detector bounding boxes'}
                </p>
              </div>
              {result.detections.length === 0 ? (
                <p className="mt-4 text-xs leading-relaxed text-slate-400">
                  No distinct foreground objects, people, or weapons were identified in this uploaded image.
                </p>
              ) : (
                <div className="mt-3 max-h-[340px] divide-y divide-slate-800/70 overflow-y-auto pr-1">
                  {result.detections.map((det, idx) => {
                    const meta = detectionMarkerIds[idx];
                    const nodeId = meta.markerId;
                    const isSelected = Boolean(nodeId && nodeId === selectedNodeId);
                    return (
                      <button
                        key={`${det.label}_${idx}`}
                        type="button"
                        disabled={!nodeId}
                        onClick={() => {
                          if (nodeId) {
                            setSelectedNodeId(nodeId === selectedNodeId ? null : nodeId);
                          }
                        }}
                        className={`flex w-full flex-col gap-0.5 py-2.5 text-left text-xs transition ${
                          isSelected
                            ? 'text-sky-300'
                            : nodeId
                            ? 'text-slate-300 hover:text-white'
                            : 'cursor-default text-slate-400'
                        }`}
                      >
                        <div className="flex w-full items-center justify-between gap-2">
                          <span>
                            <span className="font-mono text-amber-400 tabular-nums">
                              {meta.markerNumber ? `#${meta.markerNumber}` : '—'}
                            </span>{' '}
                            <span className="font-medium capitalize">{det.label}</span>{' '}
                            <span className="text-slate-500">· {det.category}</span>
                          </span>
                          <span className="shrink-0 font-mono text-[11px] text-slate-400 tabular-nums">
                            {det.confidence !== null
                              ? `${det.confidence_simulated ? 'Est. ' : ''}${(det.confidence * 100).toFixed(0)}%`
                              : 'Score N/A'}
                          </span>
                        </div>
                        {det.observation_note && (
                          <div className="text-[11px] text-slate-400">{det.observation_note}</div>
                        )}
                        {!det.normalized_bbox && (
                          <div className="font-mono text-[10px] text-amber-400/80">
                            Bounding box unavailable
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </section>

          {/* 3 Investigative Scenario Hypotheses */}
          {result.scenarios.length > 0 && (
            <section className="rounded-lg border border-slate-800 bg-[#111827] p-5">
              <div className="border-b border-slate-800/80 pb-3">
                <h3 className="text-sm font-semibold text-slate-100">
                  Grounded Scene Interpretations &amp; Hypotheses
                </h3>
                <p className="mt-0.5 text-xs text-slate-400">{result.ethical_notice}</p>
              </div>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
                {result.scenarios.map((sc, i) => (
                  <div
                    key={i}
                    className="rounded border border-slate-800 bg-slate-950/60 p-4"
                  >
                    <div className="font-mono text-xs font-medium text-sky-400 tabular-nums">
                      {sc.title}
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-slate-300">{sc.description}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Grounded Forensic Chat */}
          <ForensicChatPanel
            key={result.session_id}
            mode="image"
            sessionId={result.session_id}
            suggestions={[
              'Summarize what is visible in this uploaded image.',
              'Which objects, people, or weapons were observed?',
              'Describe the environment and scene conditions.',
              'Compare the three scene interpretations.',
            ]}
          />
        </>
      )}
    </div>
  );
};
