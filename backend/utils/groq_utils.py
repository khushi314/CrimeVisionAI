"""
Groq LLM client helper for deterministic forensic reasoning, caption refinement,
crime sequence classification, scenario generation, and grounded RAG chat.
"""

from typing import Dict, Any, Optional

try:
    from backend.config import MODEL_CONFIG
    from backend.utils.logger import setup_logger
except ImportError:
    from config import MODEL_CONFIG
    from utils.logger import setup_logger

logger = setup_logger("groq_utils")

_GROQ_CLIENT: Optional[Any] = None


def get_config() -> Dict[str, Any]:
    """Return Groq LLM configuration dictionary."""
    return {
        "groq_api_key": MODEL_CONFIG["groq"]["api_key"],
        "groq_model": MODEL_CONFIG["groq"]["model"],
        "temperature": MODEL_CONFIG["groq"]["temperature"],
        "max_tokens": MODEL_CONFIG["groq"]["max_tokens"],
    }


def get_groq_client() -> Optional[Any]:
    """
    Lazily initialize and return the global Groq client if GROQ_API_KEY is configured
    and the `groq` SDK is installed. Returns None when running offline so callers
    can execute deterministic local fallback synthesis without crashing.
    """
    global _GROQ_CLIENT
    if _GROQ_CLIENT is not None:
        return _GROQ_CLIENT

    api_key = MODEL_CONFIG["groq"].get("api_key", "").strip()
    if not api_key or api_key == "YOUR_GROQ_API_KEY_HERE":
        logger.info("GROQ_API_KEY not set; using deterministic local reasoning fallback.")
        return None

    try:
        from groq import Groq
        _GROQ_CLIENT = Groq(api_key=api_key)
        return _GROQ_CLIENT
    except ImportError:
        logger.warning("`groq` package not installed; using deterministic local reasoning fallback.")
        return None
    except Exception as exc:
        logger.error("Failed to initialize Groq client: %s", exc)
        return None


def generate_grounded_completion(prompt: str, system_prompt: str = "", temperature: float = 0.1) -> Optional[str]:
    """Execute a low-temperature Groq chat completion, returning None if unavailable."""
    client = get_groq_client()
    if client is None:
        return None

    cfg = get_config()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model=cfg["groq_model"],
            messages=messages,
            temperature=temperature,
            max_tokens=cfg["max_tokens"],
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("Groq completion request failed: %s", exc)
        return None
