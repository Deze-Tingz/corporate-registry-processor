import json
import logging
import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.classification import Classification
from app.models.document import Document
from app.services import audit_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a document classifier for the BVI Financial Services Commission's Corporate Registry.

Given the extracted text of a submitted document, you must:
1. Classify the document type
2. Extract key fields
3. Provide a confidence score and reasoning

DOCUMENT TYPES (pick exactly one):
- articles_of_incorporation
- amendment
- annual_return
- registered_agent_change
- dissolution_notice
- other

FIELDS TO EXTRACT (return null if not found):
- company_name: The registered company name
- registration_number: The BVI company registration number
- date_of_filing: The date the document was filed (ISO 8601)
- effective_date: The date the action takes effect (ISO 8601)
- registered_agent: Name of the registered agent
- signatories: List of signatory names
- jurisdiction: The jurisdiction referenced

Respond with ONLY a JSON object in this exact format:
{
  "document_type": "<type>",
  "confidence_score": <float between 0.0 and 1.0>,
  "reasoning": "<brief explanation of classification>",
  "extracted_fields": {
    "company_name": "<value or null>",
    "registration_number": "<value or null>",
    "date_of_filing": "<value or null>",
    "effective_date": "<value or null>",
    "registered_agent": "<value or null>",
    "signatories": ["<name>"] or null,
    "jurisdiction": "<value or null>"
  },
  "limitations": "<any caveats about the extraction, or null>"
}"""

PROMPT_VERSION = "1.0"


async def classify_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> Classification:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise ValueError(f"Document {document_id} not found")

    # Check if already classified
    existing = await db.execute(
        select(Classification).where(Classification.document_id == document_id)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Document {document_id} already classified")

    text = doc.extracted_text or ""
    if not text.strip():
        text = "(No text could be extracted from this document)"

    start_ms = time.monotonic()
    ai_available = True
    raw_response = None

    try:
        parsed, raw_response = await _call_claude(text)
        elapsed_ms = int((time.monotonic() - start_ms) * 1000)
    except Exception as e:
        logger.error("Claude API call failed for document %s: %s", document_id, e)
        ai_available = False
        elapsed_ms = int((time.monotonic() - start_ms) * 1000)
        parsed = _fallback_classification()

    classification = Classification(
        document_id=document_id,
        document_type=parsed["document_type"],
        confidence_score=parsed["confidence_score"],
        reasoning=parsed["reasoning"],
        extracted_fields=parsed["extracted_fields"],
        limitations=parsed.get("limitations"),
        model_version=settings.claude_model,
        prompt_version=PROMPT_VERSION,
        ai_available=ai_available,
        processing_time_ms=elapsed_ms,
        raw_response=raw_response,
    )
    db.add(classification)

    doc.status = "classified"
    await db.flush()

    await audit_service.log_action(
        db,
        action="document_classified",
        resource_type="document",
        resource_id=document_id,
        user_id=user_id,
        details={
            "document_type": parsed["document_type"],
            "confidence": parsed["confidence_score"],
            "ai_available": ai_available,
            "processing_time_ms": elapsed_ms,
        },
    )
    await db.commit()
    await db.refresh(classification)
    return classification


async def _call_claude(text: str) -> tuple[dict, dict]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Classify this document:\n\n{text[:8000]}"}
        ],
    )

    raw = {"id": message.id, "model": message.model, "usage": dict(message.usage)}
    response_text = message.content[0].text

    # Parse JSON from response
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if match:
            parsed = json.loads(match.group(1))
        else:
            raise ValueError(f"Could not parse JSON from Claude response: {response_text[:200]}")

    # Validate required fields
    parsed.setdefault("document_type", "other")
    parsed.setdefault("confidence_score", 0.5)
    parsed.setdefault("reasoning", "")
    parsed.setdefault("extracted_fields", {})

    parsed["confidence_score"] = max(0.0, min(1.0, float(parsed["confidence_score"])))

    return parsed, raw


def _fallback_classification() -> dict:
    return {
        "document_type": "other",
        "confidence_score": 0.0,
        "reasoning": "AI classification unavailable — queued for manual review",
        "extracted_fields": {},
        "limitations": "Automatic classification failed. Manual review required.",
    }
