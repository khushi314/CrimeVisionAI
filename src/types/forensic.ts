export type ModalityTab = 'image' | 'audio' | 'video' | 'fusion';

export interface DetectionItem {
  label: string;
  raw_label?: string;
  category: 'person' | 'weapon' | 'object';
  confidence: number | null;
  bbox: number[] | null;
  normalized_bbox: number[] | null;
  bbox_simulated?: boolean;
  confidence_simulated?: boolean;
  observation_note?: string;
}

export interface Object3DNode {
  id: string;
  marker_number: number;
  label: string;
  category: 'person' | 'weapon' | 'object';
  confidence: number | null;
  position: {x: number; y: number; z: number};
  scale: number;
  bbox: number[];
  simulated_projection?: boolean;
}

export interface Scene3DData {
  room_type: string;
  dimensions: {width: number; height: number; depth: number};
  objects: Object3DNode[];
  is_simulated?: boolean;
}

export interface ScenarioHypothesis {
  title: string;
  description: string;
}

export interface ImageAnalysisProvenance {
  model: string;
  analysis_mode: 'multimodal_vision_vlm' | 'calibrated_detector';
  bbox_source: 'vlm_estimated' | 'detector_calibrated' | 'unavailable';
  confidence_source: 'vlm_estimated' | 'detector_calibrated' | 'unavailable';
  spatial_3d_source: 'simulated_from_2d' | 'unavailable';
  image_dimensions: {width: number; height: number};
  disclaimer: string;
}

export interface ImageForensicResult {
  session_id: string;
  mode: 'image';
  file_name?: string;
  sha256?: string;
  media_url?: string;
  ai_scene_summary: {
    summary_type: string;
    brief_description: string;
  };
  visual_summary: string;
  counts: {
    objects: number;
    persons: number;
    weapons: number;
  };
  location: string;
  location_confidence: number | null;
  actions_detected: string[];
  evidence_facts: string[];
  detections: DetectionItem[];
  scenarios: ScenarioHypothesis[];
  scene_3d: Scene3DData;
  provenance?: ImageAnalysisProvenance;
  ethical_notice: string;
}

export interface TimelineEntry {
  time: string;
  seconds: number;
  event: string;
  confidence?: number;
  severity?: 'normal' | 'elevated' | 'alert';
  modality?: string;
  certainty?: 'high' | 'medium' | 'low';
  temporal_uncertainty?: 'known' | 'unknown';
}

export interface AudioForensicResult {
  session_id: string;
  mode: 'audio';
  file_name?: string;
  sha256?: string;
  media_url?: string;
  duration_seconds: number;
  transcript: string;
  ai_summary: string;
  event_type: string;
  location: string;
  translations: {
    english: string;
    hindi: string;
    telugu: string;
    french: string;
  };
  timeline: TimelineEntry[];
  facts: {
    who: string[];
    where: string[];
    when: string[];
    actions: string[];
    locations: string[];
    suspect_description: string;
  };
  ethical_notice: string;
}

export interface VideoForensicResult {
  session_id: string;
  mode: 'video';
  file_name?: string;
  sha256?: string;
  media_url?: string;
  duration_seconds: number;
  frames_analyzed?: number;
  classification: string;
  classification_reason: string;
  classification_confidence: number;
  visual_summary: string;
  scene_intelligence: {
    objects_detected: string[];
    people_count: number;
    weapons_count: number;
    location: string;
    action: string;
  };
  timeline: TimelineEntry[];
  ethical_notice: string;
}

export interface FusionForensicResult {
  session_id: string;
  mode: 'fusion';
  modalities_fused: string[];
  consistency: {
    overall_score: number;
    matches: string[];
    conflicts: string[];
  };
  unified_timeline: TimelineEntry[];
  scenarios: Array<string | ScenarioHypothesis>;
  ethical_notice: string;
}

export interface SampleAssetItem {
  id: string;
  label: string;
  filename: string;
  url: string;
  description: string;
}

export interface SamplesCatalog {
  image: SampleAssetItem[];
  audio: SampleAssetItem[];
  video: SampleAssetItem[];
}

export interface SessionHistoryItem {
  session_id: string;
  mode: string;
  created_at_utc: string;
  file_name?: string;
  location?: string;
}
