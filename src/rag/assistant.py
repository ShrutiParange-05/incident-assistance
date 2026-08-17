"""
GenAI Assistant (the final box in the architecture diagram).

Takes the classifier's output (error_type, probable_cause) plus the
raw incident, retrieves relevant runbook context via RAG, and asks
Claude to turn that into one concrete, actionable recommendation.

Falls back to a deterministic, non-LLM recommendation if no API key
is configured, so the app runs (and its tests pass) without network
access or a paid key.
"""
import logging

from anthropic import Anthropic

from src.config import get_settings
from src.error_classifier import Classification
from src.rag.retriever import retrieve

logger = logging.getLogger("incident_assistant")

SYSTEM_PROMPT = (
    "You are an SRE assistant. You are given a production incident, its "
    "automated classification, and relevant runbook excerpts. Respond with "
    "ONE short, concrete, actionable recommended step an on-call engineer "
    "should take right now. Maximum 2 sentences. No preamble, no markdown, "
    "just the recommendation."
)


def _fallback_recommendation(classification: Classification, context_docs: list[dict]) -> str:
    """Deterministic recommendation used when no LLM is available."""
    if context_docs:
        return f"Check the '{context_docs[0]['title']}' runbook: {context_docs[0]['content'].split('.')[0]}."
    return f"Investigate '{classification.error_type}': {classification.probable_cause}."


def generate_recommendation(
    service: str,
    error_code: int,
    message: str,
    classification: Classification,
) -> tuple[str, list[str]]:
    """
    Returns (recommended_action, source_doc_ids).
    """
    query = f"{classification.error_type} {classification.probable_cause} {message}"
    context_docs = retrieve(query, top_k=3)
    source_ids = [doc["id"] for doc in context_docs]

    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.warning("No ANTHROPIC_API_KEY configured — using fallback recommendation")
        return _fallback_recommendation(classification, context_docs), source_ids

    context_block = "\n\n".join(
        f"[{doc['id']}] {doc['title']}\n{doc['content']}" for doc in context_docs
    ) or "No matching runbook found."

    user_prompt = (
        f"Incident:\n"
        f"- service: {service}\n"
        f"- error_code: {error_code}\n"
        f"- message: {message}\n\n"
        f"Automated classification:\n"
        f"- error_type: {classification.error_type}\n"
        f"- probable_cause: {classification.probable_cause}\n"
        f"- severity: {classification.severity}\n\n"
        f"Relevant runbook excerpts:\n{context_block}\n\n"
        f"Give one concrete recommended action."
    )

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text_blocks = [block.text for block in response.content if block.type == "text"]
        recommendation = " ".join(text_blocks).strip()
        return recommendation or _fallback_recommendation(classification, context_docs), source_ids
    except Exception:
        logger.exception("GenAI assistant call failed — falling back to rule-based recommendation")
        return _fallback_recommendation(classification, context_docs), source_ids
