# import os
# import json
# import logging
# from dataclasses import dataclass
# from typing import Optional, Dict, Any
# from app.config import settings

# logger = logging.getLogger(__name__)


# @dataclass
# class AIAnalysisResult:
#     """
#     Standardized data class returned by the AI pipeline orchestration boundary.
#     Reconciles field naming differences between AI output ('recommended_action')
#     and database model ('ai_action_plan').
#     """
#     is_valid_civic_issue: bool
#     category: str
#     severity: str
#     reasoning: str
#     ai_action_plan: str
#     translated_text: Optional[str] = None
#     raw_ai_response: Optional[Dict[str, Any]] = None


# # ==============================================================================
# # INTEGRATION STUB: Syed Fazeel's Audio AI (Whisper)
# # ==============================================================================
# def transcribe_and_translate_audio(audio_path: Optional[str]) -> Optional[str]:
#     """
#     Integration Stub for Whisper Audio Processing.

#     Takes a local voice note audio file in Urdu / Roman Urdu / English,
#     transcribes it, and translates it into clear English text.

#     :param audio_path: Filesystem path to the saved audio file.
#     :return: Translated English string, or None if no audio provided.
#     """
#     if not audio_path or not os.path.exists(audio_path):
#         return None

#     # Hook for Syed Fazeel's Whisper module:
#     # Example:
#     #   import whisper
#     #   model = whisper.load_model(settings.WHISPER_MODEL_SIZE)
#     #   result = model.transcribe(audio_path, task="translate")
#     #   return result.get("text", "").strip()

#     logger.info(f"[AI STUB] Transcribing and translating audio file: {audio_path}")
#     path_lower = audio_path.lower()
#     if "pothole" in path_lower or "sarak" in path_lower or "road" in path_lower:
#         return "Deep pothole on broken road causing hazard."
#     elif "sewer" in path_lower or "gatar" in path_lower or "drain" in path_lower:
#         return "Sewerage water overflowing from blocked drain."
#     elif "garbage" in path_lower or "kachra" in path_lower:
#         return "Reported overflowing garbage pile near the street corner requiring cleanup."

#     return "Voice report describing civic issue requiring municipal cleanup."


# # ==============================================================================
# # INTEGRATION STUB: Syed Fazeel's Multimodal Vision & Logic AI
# # ==============================================================================
# def analyze_civic_issue(
#     image_path: str,
#     translated_text: Optional[str] = None,
#     user_description: Optional[str] = None
# ) -> AIAnalysisResult:
#     """
#     Integration Stub for Multimodal Vision + Logic AI (Gemini / Qoder / Llama-3.2 Vision).

#     Sends the image and contextual description to the Vision LLM with strict JSON prompting:
#     Target JSON Output from AI:
#     {
#         "is_valid_civic_issue": bool,
#         "category": "Garbage" | "Pothole" | "Sewerage",
#         "severity": "Critical" | "High" | "Medium" | "Low",
#         "reasoning": str,
#         "recommended_action": str
#     }

#     Reconciles 'recommended_action' -> 'ai_action_plan' at this boundary.

#     :param image_path: Local filesystem path to the uploaded image.
#     :param translated_text: English text obtained from Whisper transcription.
#     :param user_description: Optional raw text entered by citizen.
#     :return: AIAnalysisResult instance.
#     """
#     combined_context = f"{translated_text or ''} {user_description or ''}".strip().lower()

#     # 1. Check if an external ai_engine module exists in project root (Syed Fazeel's script)
#     try:
#         import ai_engine  # type: ignore
#         if hasattr(ai_engine, "analyze_submission"):
#             logger.info("[AI ENGINE] Invoking custom ai_engine.analyze_submission...")
#             raw_res = ai_engine.analyze_submission(image_path, combined_context)
#             return AIAnalysisResult(
#                 is_valid_civic_issue=raw_res.get("is_valid_civic_issue", True),
#                 category=raw_res.get("category", "Garbage"),
#                 severity=raw_res.get("severity", "High"),
#                 reasoning=raw_res.get("reasoning", "Processed by custom AI engine."),
#                 ai_action_plan=raw_res.get("recommended_action") or raw_res.get("ai_action_plan", "Standard municipal response dispatched."),
#                 translated_text=translated_text,
#                 raw_ai_response=raw_res
#             )
#     except ImportError:
#         pass  # ai_engine not yet mounted, fallback to built-in provider or mock
#     except Exception as e:
#         logger.error(f"[AI ENGINE ERROR] Custom ai_engine failed: {e}. Falling back to default heuristics.")

#     # 2. Intelligent Hackathon Heuristic / Offline Mock Provider
#     # This guarantees 100% test passing and seamless demo presentation even if offline.
#     category = "Garbage"
#     severity = "High"
#     reasoning = "Accumulated waste and debris observed in public walkway."
#     recommended_action = "Requires 1 dump truck and 3 sanitation workers for 2 hours."
#     is_valid = True

#     if "selfie" in combined_context or "blank" in combined_context or "fake" in combined_context or "spam" in combined_context:
#         is_valid = False
#         category = "Unassigned"
#         severity = "Low"
#         reasoning = "Image or description flagged as unrelated to civic infrastructure."
#         recommended_action = "No municipal action required."
#     elif any(k in combined_context for k in ["garbage", "kachra", "trash", "waste", "dump", "debris", "litter", "rubbish"]):
#         category = "Garbage"
#         severity = "Critical" if any(k in combined_context for k in ["huge", "massive", "toxic", "blocking", "severe"]) else "High"
#         reasoning = "Garbage accumulation and refuse requiring municipal sanitation clearance."
#         recommended_action = "Requires 1 dump truck and 3 sanitation workers for 2 hours."
#     elif any(k in combined_context for k in ["pothole", "gaddha", "crater", "tooti hui", "tooti sarak", "broken road", "damaged road", "road damage", "asphalt"]):
#         category = "Pothole"
#         severity = "Critical" if any(k in combined_context for k in ["deep", "huge", "dangerous", "severe", "broken"]) else "High"
#         reasoning = "Severe road surface fracture posing danger to two-wheelers and traffic."
#         recommended_action = "Requires 1 asphalt patcher truck and 2 road repair technicians."
#     elif any(k in combined_context for k in ["sewer", "gatar", "gutter", "drain", "sewage", "sewerage", "naali", "manhole", "ganda paani"]):
#         category = "Sewerage"
#         severity = "Critical"
#         reasoning = "Sewerage line blockage causing contaminated water overflow on public road."
#         recommended_action = "Requires 1 suction jetting machine truck and 2 drainage specialists."
#     else:
#         # Default fallback
#         category = "Garbage"
#         severity = "Medium"
#         reasoning = "Civic cleanliness concern reported in public area."
#         recommended_action = "Requires sanitation inspection and standard clearance team."

#     return AIAnalysisResult(
#         is_valid_civic_issue=is_valid,
#         category=category,
#         severity=severity,
#         reasoning=reasoning,
#         ai_action_plan=recommended_action,
#         translated_text=translated_text or user_description,
#         raw_ai_response={
#             "is_valid_civic_issue": is_valid,
#             "category": category,
#             "severity": severity,
#             "reasoning": reasoning,
#             "recommended_action": recommended_action
#         }
#     )


# # ==============================================================================
# # PIPELINE ORCHESTRATION FUNCTION
# # ==============================================================================
# def process_civic_submission(
#     image_path: str,
#     audio_path: Optional[str] = None,
#     user_description: Optional[str] = None
# ) -> AIAnalysisResult:
#     """
#     Main orchestration entrypoint for processing citizen reports.
#     Executes Audio STT (Whisper) -> Multimodal Vision & Logic classification.
#     """
#     # Step 1: Transcribe and translate voice note if present
#     translated_audio_text = None
#     if audio_path:
#         translated_audio_text = transcribe_and_translate_audio(audio_path)

#     # Step 2: Combine translated audio with any typed description
#     final_text = translated_audio_text or user_description

#     # Step 3: Run Multimodal Vision LLM classification
#     result = analyze_civic_issue(
#         image_path=image_path,
#         translated_text=final_text,
#         user_description=user_description
#     )

#     if translated_audio_text and not result.translated_text:
#         result.translated_text = translated_audio_text

#     return result

# app/ai_integration.py
# ==============================================================================
# AI Pipeline Integration — CleanCity Copilot
# Delegates entirely to ai_engine.py (Whisper + Gemini 2.5 Flash).
# No mock heuristics. Fails gracefully with a safe fallback AIAnalysisResult.
# ==============================================================================

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


# ==============================================================================
# ENGINE IMPORT (once at module load — fail fast, log clearly)
# ==============================================================================
try:
    import ai_engine as _ai_engine
    _AI_ENGINE_AVAILABLE = True
    logger.info("ai_engine.py loaded successfully — real AI pipeline active.")
except ImportError as _err:
    _ai_engine = None  # type: ignore[assignment]
    _AI_ENGINE_AVAILABLE = False
    logger.critical(
        "Could not import ai_engine.py: %s. "
        "Ensure ai_engine.py is in the project root and all its dependencies are installed. "
        "Real AI processing is unavailable until this is resolved.",
        _err,
    )


# ==============================================================================
# RESULT DATACLASS
# ==============================================================================
@dataclass
class AIAnalysisResult:
    """
    Standardised return type for the AI pipeline.
    'ai_action_plan' reconciles the engine's 'recommended_action' key with
    the database column name used throughout the rest of the application.
    """
    is_valid_civic_issue: bool
    category: str
    severity: str
    reasoning: str
    ai_action_plan: str
    translated_text: Optional[str] = None
    raw_ai_response: Optional[Dict[str, Any]] = None


# ==============================================================================
# SAFE FALLBACK FACTORY
# ==============================================================================
def _fallback_result(
    text_description: Optional[str] = None,
    reason: str = "AI engine unavailable or failed — manual review required.",
) -> AIAnalysisResult:
    """
    Returns a safe, conservative AIAnalysisResult used whenever the real engine
    cannot be reached or raises an exception. Marks the issue as valid so it is
    not silently dropped, but leaves category/severity as Unassigned/Unknown so
    a human reviewer knows it was never actually classified.
    """
    return AIAnalysisResult(
        is_valid_civic_issue=True,
        category="Unassigned",
        severity="Unknown",
        reasoning=reason,
        ai_action_plan="Route to municipal supervisor for manual assessment.",
        translated_text=text_description or None,
        raw_ai_response=None,
    )


# ==============================================================================
# AUDIO TRANSCRIPTION  (Whisper via ai_engine.transcribe_audio)
# ==============================================================================
def transcribe_and_translate_audio(audio_path: Optional[str]) -> Optional[str]:
    """
    Transcribes a voice note to English text using ai_engine.transcribe_audio().

    Returns None when:
      - audio_path is None or empty string
      - the file does not exist on disk
      - ai_engine is unavailable
      - the engine raises any exception
    """
    if not audio_path:
        logger.debug("transcribe_and_translate_audio: audio_path is None — skipping.")
        return None

    if not os.path.exists(audio_path):
        logger.warning(
            "transcribe_and_translate_audio: file not found on disk: %s", audio_path
        )
        return None

    if not _AI_ENGINE_AVAILABLE:
        logger.error(
            "transcribe_and_translate_audio: ai_engine is unavailable — "
            "cannot transcribe %s.",
            audio_path,
        )
        return None

    try:
        transcript: str = _ai_engine.transcribe_audio(audio_path)
        logger.info(
            "transcribe_and_translate_audio: transcription succeeded for %s", audio_path
        )
        return transcript.strip() if transcript else None
    except Exception as exc:
        logger.exception(
            "transcribe_and_translate_audio: transcription failed for %s: %s",
            audio_path,
            exc,
        )
        return None


# ==============================================================================
# IMAGE + TEXT ANALYSIS  (Gemini 2.5 Flash via ai_engine.analyze_civic_issue)
# ==============================================================================
def analyze_civic_issue(
    image_path: str,
    translated_text: Optional[str] = None,
    user_description: Optional[str] = None,
) -> AIAnalysisResult:
    """
    Classifies a civic issue from an image and optional text context using
    ai_engine.analyze_civic_issue(image_path, text_description) -> dict.

    Expected keys in the returned dict:
        is_valid_civic_issue (bool)
        category             (str)  — "Garbage" | "Pothole" | "Sewerage" | "Unassigned"
        severity             (str)  — "Critical" | "High" | "Medium" | "Low" | "Unknown"
        reasoning            (str)
        recommended_action   (str)  — mapped to AIAnalysisResult.ai_action_plan
        translated_text      (str, optional)

    Any missing key falls back to a safe default; any exception returns a
    fallback AIAnalysisResult rather than propagating upward.
    """
    text_description: str = (translated_text or user_description or "").strip()

    if not _AI_ENGINE_AVAILABLE:
        logger.error(
            "analyze_civic_issue: ai_engine unavailable — returning safe fallback "
            "for image: %s",
            image_path,
        )
        return _fallback_result(
            text_description,
            reason="AI engine (ai_engine.py) could not be imported — manual review required.",
        )

    try:
        raw: Dict[str, Any] = _ai_engine.analyze_civic_issue(
            image_path=image_path,
            text_description=text_description,
        )
        logger.info(
            "analyze_civic_issue: Gemini analysis succeeded for image: %s", image_path
        )

        # 'recommended_action' is the engine's output key; 'ai_action_plan' is the
        # internal/database field name.  Accept either so the boundary is explicit.
        ai_action_plan: str = (
            raw.get("recommended_action")
            or raw.get("ai_action_plan")
            or "Refer to municipal department for assessment."
        )

        # Engine may return its own translated_text; fall back to what the caller supplied.
        resolved_translated_text: Optional[str] = (
            raw.get("translated_text") or text_description or None
        )

        return AIAnalysisResult(
            is_valid_civic_issue=bool(raw.get("is_valid_civic_issue", True)),
            category=str(raw.get("category", "Unassigned")),
            severity=str(raw.get("severity", "Unknown")),
            reasoning=str(raw.get("reasoning", "No reasoning returned by AI engine.")),
            ai_action_plan=str(ai_action_plan),
            translated_text=resolved_translated_text,
            raw_ai_response=raw,
        )

    except Exception as exc:
        logger.exception(
            "analyze_civic_issue: Gemini analysis failed for %s: %s", image_path, exc
        )
        return _fallback_result(
            text_description,
            reason=f"AI analysis raised {type(exc).__name__} — manual review required.",
        )


# ==============================================================================
# PIPELINE ORCHESTRATOR
# ==============================================================================
def process_civic_submission(
    image_path: str,
    audio_path: Optional[str] = None,
    user_description: Optional[str] = None,
) -> AIAnalysisResult:
    """
    Main entry point for processing a single citizen report.

    Execution order:
      1. Transcribe audio (Whisper) — skipped safely if audio_path is None/missing.
      2. Merge transcript with typed description (transcript takes priority).
      3. Classify image + merged text (Gemini 2.5 Flash).
      4. Guarantee translated_text is populated if audio was transcribed.
    """
    # Step 1: Audio → English text (None-safe; guard lives inside the function)
    translated_audio_text: Optional[str] = transcribe_and_translate_audio(audio_path)

    # Step 2: Audio transcript takes priority; typed description is the fallback
    final_text: Optional[str] = translated_audio_text or user_description

    # Step 3: Vision + LLM classification
    result: AIAnalysisResult = analyze_civic_issue(
        image_path=image_path,
        translated_text=final_text,
        user_description=user_description,
    )

    # Step 4: Back-fill translated_text if the engine didn't echo it back
    if translated_audio_text and not result.translated_text:
        result.translated_text = translated_audio_text

    return result
