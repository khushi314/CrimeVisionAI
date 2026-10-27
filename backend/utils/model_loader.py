"""
Lazy model loading utilities for RT-DETR, CLIP, BLIP, SAM, and Whisper.
Automatically detects CUDA vs CPU and gracefully falls back to lightweight
mode when running unit tests or offline without 2GB+ model checkpoints.
"""

from typing import Dict, Any, Optional

try:
    from backend.config import MODEL_CONFIG
    from backend.utils.logger import setup_logger
except ImportError:
    from config import MODEL_CONFIG
    from utils.logger import setup_logger

logger = setup_logger("model_loader")

_LOADED_MODELS: Dict[str, Any] = {}


def resolve_device() -> str:
    """Resolve PyTorch execution device ('cuda' or 'cpu')."""
    pref = MODEL_CONFIG.get("device_preference", "auto").lower()
    if pref in ("cuda", "cpu"):
        return pref
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def load_rt_detr_model() -> Optional[Dict[str, Any]]:
    """Load RT-DETR object detection processor and model from HuggingFace Transformers."""
    if MODEL_CONFIG.get("lightweight_mode"):
        return None
    if "rt_detr" in _LOADED_MODELS:
        return _LOADED_MODELS["rt_detr"]

    try:
        import torch
        from transformers import AutoImageProcessor, AutoModelForObjectDetection

        device = resolve_device()
        model_id = MODEL_CONFIG["rt_detr"]["model_id"]
        logger.info("Loading RT-DETR model (%s) on %s...", model_id, device)
        processor = AutoImageProcessor.from_pretrained(model_id)
        model = AutoModelForObjectDetection.from_pretrained(model_id).to(device)
        model.eval()
        bundle = {"processor": processor, "model": model, "device": device}
        _LOADED_MODELS["rt_detr"] = bundle
        return bundle
    except Exception as exc:
        logger.warning("RT-DETR unavailable (%s); falling back to heuristic CV detector.", exc)
        return None


def load_clip_model() -> Optional[Dict[str, Any]]:
    """Load CLIP zero-shot scene classification processor and model."""
    if MODEL_CONFIG.get("lightweight_mode"):
        return None
    if "clip" in _LOADED_MODELS:
        return _LOADED_MODELS["clip"]

    try:
        from transformers import CLIPProcessor, CLIPModel

        device = resolve_device()
        model_id = MODEL_CONFIG["clip"]["model_id"]
        logger.info("Loading CLIP model (%s) on %s...", model_id, device)
        processor = CLIPProcessor.from_pretrained(model_id)
        model = CLIPModel.from_pretrained(model_id).to(device)
        model.eval()
        bundle = {"processor": processor, "model": model, "device": device}
        _LOADED_MODELS["clip"] = bundle
        return bundle
    except Exception as exc:
        logger.warning("CLIP unavailable (%s); using fallback scene classifier.", exc)
        return None


def load_blip2_model() -> Optional[Dict[str, Any]]:
    """Load BLIP/BLIP-2 image captioning processor and model."""
    if MODEL_CONFIG.get("lightweight_mode"):
        return None
    if "blip2" in _LOADED_MODELS:
        return _LOADED_MODELS["blip2"]

    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration

        device = resolve_device()
        model_id = MODEL_CONFIG["blip2"]["model_id"]
        logger.info("Loading BLIP captioning model (%s) on %s...", model_id, device)
        processor = BlipProcessor.from_pretrained(model_id)
        model = BlipForConditionalGeneration.from_pretrained(model_id).to(device)
        model.eval()
        bundle = {"processor": processor, "model": model, "device": device}
        _LOADED_MODELS["blip2"] = bundle
        return bundle
    except Exception as exc:
        logger.warning("BLIP unavailable (%s); using structured detection captioner.", exc)
        return None


def load_sam_model() -> Optional[Any]:
    """Load optional Segment Anything (SAM) predictor if checkpoint is configured."""
    if MODEL_CONFIG.get("lightweight_mode"):
        return None
    if "sam" in _LOADED_MODELS:
        return _LOADED_MODELS["sam"]

    ckpt = MODEL_CONFIG["sam"].get("checkpoint_path", "").strip()
    if not ckpt:
        return None

    try:
        from segment_anything import sam_model_registry, SamPredictor

        device = resolve_device()
        sam = sam_model_registry[MODEL_CONFIG["sam"]["model_type"]](checkpoint=ckpt)
        sam.to(device=device)
        predictor = SamPredictor(sam)
        _LOADED_MODELS["sam"] = predictor
        return predictor
    except Exception as exc:
        logger.warning("SAM unavailable (%s); bounding-box spatial masks will be used.", exc)
        return None


def preload_models(eager: bool = False) -> Dict[str, str]:
    """
    Optionally preload models at startup or verify device readiness.
    Lazy loading (`eager=False`) keeps startup fast on student laptops.
    """
    device = resolve_device()
    status = {"device": device, "mode": "lightweight" if MODEL_CONFIG.get("lightweight_mode") else "lazy"}
    if eager and not MODEL_CONFIG.get("lightweight_mode"):
        load_rt_detr_model()
        load_clip_model()
        load_blip2_model()
        status["mode"] = "preloaded"
    logger.info("Model loader initialized: %s", status)
    return status
