"""Diagnosis adapter that exposes a safe source label for AgentOps measurements."""
import json

from loguru import logger

from app.ai import analyzer
from app.ai.confidence import apply_confidence
from app.ai.fixes import apply_fix_defaults
from app.ai.llm import LlmError, LlmNotConfiguredError
from app.ai.prompt import build_messages
from app.models.schemas import Diagnosis


def diagnose_with_metadata(investigation: dict) -> tuple[Diagnosis, str]:
    """Return a diagnosis and source label without returning prompt or log content."""
    source = "llm"
    try:
        raw = analyzer.complete(build_messages(investigation))
        diagnosis = analyzer._from_mapping(analyzer._parse_json(raw))
    except LlmNotConfiguredError:
        logger.warning("OpenRouter key missing; using local evidence correlation")
        diagnosis = analyzer.correlate_locally(investigation)
        source = "local_fallback"
    except LlmError:
        logger.error("OpenRouter failed; using local evidence correlation")
        diagnosis = analyzer.correlate_locally(investigation)
        source = "local_fallback"
    except (ValueError, json.JSONDecodeError):
        logger.error("OpenRouter returned unparseable diagnosis; using local evidence correlation")
        diagnosis = analyzer.correlate_locally(investigation)
        source = "local_fallback"

    diagnosis = apply_confidence(investigation, diagnosis)
    return apply_fix_defaults(investigation, diagnosis), source
