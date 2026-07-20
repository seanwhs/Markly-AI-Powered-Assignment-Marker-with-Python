import os
import asyncio
import logging
import re
from typing import Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI, APIError, APITimeoutError

load_dotenv()

# ---------------------------------------------------------------------------
# Multi-provider API clients
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


# Provider clients
_clients = {}

if OPENROUTER_API_KEY:
    _clients["openrouter"] = AsyncOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

if GROQ_API_KEY:
    _clients["groq"] = AsyncOpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

if GEMINI_API_KEY:
    _clients["gemini"] = AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

if MISTRAL_API_KEY:
    _clients["mistral"] = AsyncOpenAI(
        api_key=MISTRAL_API_KEY,
        base_url="https://api.mistral.ai/v1"
    )

# Default client (OpenRouter)
client = _clients.get("openrouter")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model routing: determine provider from model name
# ---------------------------------------------------------------------------
def _get_client_for_model(model_name: str):
    """Return the appropriate API client for a given model name."""
    model_lower = model_name.lower()

    # Groq models (no slash, typically llama/mixtral/gemma without provider prefix)
    if model_lower.startswith(("llama-3", "mixtral", "gemma-", "llama3")) and "/" not in model_name:
        return _clients.get("groq", client)

    # Gemini models
    if model_lower.startswith("gemini-"):
        return _clients.get("gemini", client)

    # Mistral models
    if model_lower.startswith(("mistral", "codestral", "pixtral", "ministral")):
        return _clients.get("mistral", client)

    # OpenRouter models (have provider/model format with "/")
    if "/" in model_name:
        return _clients.get("openrouter", client)

    # Default fallback
    return client


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SUBJECT_DETECTION_PROMPT = """
You are an academic subject classifier.

Choose ONLY one: Mathematics, English, Science, Programming.

Key distinctions:
- Mathematics: arithmetic, algebra, geometry, trigonometry, calculus, word problems about pure math, equations, solving for variables, number theory, statistics/probability, graphs of mathematical functions, step-by-step numeric equations, arithmetic operations, and formula evaluations.
- Science: biology, chemistry, physics, scientific method, experiments, hypotheses, lab reports, natural phenomena, anatomy, ecosystems, chemical reactions, forces, energy, cells, organisms.
- English: essays, literature, grammar, reading comprehension, poetry, creative writing, vocabulary, language arts, book reports.
- Programming: code, algorithms, programming languages (Python, Java, etc.), software development, debugging, functions, loops, data structures.

CRITICAL RULE FOR ACCURACY:
- If an assignment consists of step-by-step numbers, pure calculation workloads, algebraic manipulations, or arithmetic solving, it MUST be classified as Mathematics. Only classify as Science if the core task requires explaining or evaluating empirical scientific concepts (e.g., cell structure, photosynthesis, chemical reactions, ecosystems, or physical laws) rather than performing numeric arithmetic.

Return ONLY the single word. No explanation.

Assignment:
"""

JSON_SCHEMA_PROMPT = """
You are a teacher marking an assignment.

You MUST annotate densely across the entire page. Every question should get attention.

IMPORTANT — Balance your annotations:
- Use ticks for every correct answer or correct step
- Use crosses for mistakes
- Use praise for good work (e.g. "Great work!", "Well explained", "Perfect")
- Use corrections to fix errors
- Use comments for short explanations
- Use margin_note for side observations
- Use summary only once at the bottom

Return ONLY valid JSON matching the format below.
DO NOT include markdown code blocks (like ```json) or extra text.

JSON FORMAT:
{
  "grade": "X/10",
  "overall_feedback": "short teacher summary",
  "marks": [
    {
      "type": "tick",
      "bbox": [ymin, xmin, ymax, xmax],
      "text": "short handwritten teacher note"
    }
  ]
}

CRITICAL bbox rules:
- MUST be normalized 0–1000
- format: [ymin, xmin, ymax, xmax]

Teacher style:
- very short handwriting style notes
- mix of positive and corrective feedback
- example notes: "Good", "Wrong", "Great!", "Check sign", "Redo", "Correct", "Explain better", "Well done", "Almost", "Right"
"""

MATH_MARKING_PROMPT = "You are a mathematics teacher. Mark every step carefully. Acknowledge correct work with ticks and praise."
ENGLISH_MARKING_PROMPT = "You are an English teacher. Mark grammar, clarity, structure. Note strengths as well as areas to improve."
SCIENCE_MARKING_PROMPT = "You are a science teacher. Check accuracy and reasoning. Highlight what is correct and what needs fixing."
PROGRAMMING_MARKING_PROMPT = "You are a programming instructor. Check logic, correctness, structure. Mark correct code and errors alike."
GENERIC_MARKING_PROMPT = "You are a teacher. Mark thoroughly, with ticks for correct answers and crosses for mistakes."

SUBJECT_PROMPTS = {
    "Mathematics": MATH_MARKING_PROMPT,
    "English": ENGLISH_MARKING_PROMPT,
    "Science": SCIENCE_MARKING_PROMPT,
    "Programming": PROGRAMMING_MARKING_PROMPT,
}

VISION_PROMPT = "Analyze the assignment and mark it with ticks for correct work, crosses for mistakes, and short teacher-style notes throughout."

# ---------------------------------------------------------------------------
# Model pools — expanded with free models from all providers
# ---------------------------------------------------------------------------

# Primary text-judging pool (raced concurrently)
MODELS_POOL = [
    # OpenRouter paid
    "openai/gpt-4o-mini",
    "qwen/qwen-2.5-coder-7b-instruct",
    "google/gemma-2-9b-it",
    "meta-llama/llama-3.3-70b-instruct",
    # OpenRouter free
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter/free",
    "qwen/qwen-3.6-coder",
    "deepseek/deepseek-r1",
    # Groq (fast, free tier)
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    # Gemini (Google)
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro",
    # Mistral
    "codestral-latest",
]

# Free fallback text models (tried sequentially when credits exhausted)
FREE_TEXT_MODELS = [
    # OpenRouter free tier
    "openrouter/free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-31b-it:free",
    "meta-ama/llama-3.2-3b-instruct:free",
    # Groq free tier
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    # Gemini (has generous free tier)
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
]

# Free fallback image/vision models
FREE_IMAGE_MODELS = [
    "openrouter/free",
    "google/gemma-4-31b-it:free",
    "gemini-3.5-flash",          # Gemini has vision
    "gemini-3.1-pro",            # Gemini has vision
]

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


# ---------------------------------------------------------------------------
# JSON / Grade utilities
# ---------------------------------------------------------------------------
def _extract_json(raw: str) -> str:
    """Extract JSON object from a string, stripping markdown fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.lstrip("`").lstrip("json").lstrip("`").strip()
    if raw.endswith("```"):
        raw = raw.rstrip("`").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end+1]
    return raw


def extract_grade(text: str) -> str:
    """Extract a grade string from AI-generated text using regex patterns."""
    if not text:
        return "N/A"
    patterns = [
        r"\b(\d{1,2}(?:\.\d+)?)\s*/\s*10\b",
        r"\bGrade[:\s]*([A-F][+-]?)\b",
        r"\b(\d{1,2}(?:\.\d+)?)\s*/\s*(?:100|20|50)\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            if "Grade" in pat:
                return m.group(1)
            return m.group(0).replace(" ", "")
    return "N/A"


# ---------------------------------------------------------------------------
# Subject detection
# ---------------------------------------------------------------------------
async def detect_subject(content: str) -> tuple[str, str | None]:
    """Detect the academic subject of an assignment using AI."""
    try:
        response = await client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": SUBJECT_DETECTION_PROMPT + content}],
            temperature=0
        )
        subject = response.choices[0].message.content.strip()
        valid_subjects = {"Mathematics", "English", "Science", "Programming"}
        if subject in valid_subjects:
            return subject, None
        reason = f"Subject detection returned invalid subject: {subject!r}"
        logger.error(reason)
        return "Mathematics", reason
    except (APITimeoutError, APIError) as exc:
        reason = f"Subject detection API error: {exc}"
        logger.error(reason)
        return "Mathematics", reason
    except Exception as exc:
        reason = f"Unexpected error in subject detection: {exc}"
        logger.exception(reason)
        return "Mathematics", reason


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------
def _is_credit_error(exc: Exception) -> bool:
    """Check if an exception is a 402 credit/insufficient-funds error."""
    msg = str(exc)
    return "402" in msg or "requires more credits" in msg or "insufficient" in msg.lower()


def _is_rate_limit(exc: Exception) -> bool:
    """Check if an exception is a rate-limit (429) error."""
    msg = str(exc)
    return "429" in msg or "rate limit" in msg.lower() or "too many requests" in msg.lower()


# ---------------------------------------------------------------------------
# Core AI call with multi-provider support
# ---------------------------------------------------------------------------
async def ask_ai(prompt: str, model_name: str, timeout: float = 10.0) -> str:
    """Send a single prompt to a specific AI model with retry logic.

    Automatically routes to the correct provider client based on model name.
    """
    model_client = _get_client_for_model(model_name)
    if model_client is None:
        logger.error(f"No API client available for model {model_name}")
        return ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await asyncio.wait_for(
                model_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                ),
                timeout=timeout
            )
            result = response.choices[0].message.content
            if result:
                return result
            logger.warning(f"Empty response from {model_name} on attempt {attempt}")
        except asyncio.TimeoutError:
            logger.warning(f"Timeout calling {model_name} (attempt {attempt}/{MAX_RETRIES})")
        except (APITimeoutError, APIError) as exc:
            if _is_credit_error(exc):
                logger.warning(f"Credit limit for {model_name}, trying free fallback...")
                return await _try_free_text_models(prompt, timeout)
            if _is_rate_limit(exc):
                logger.warning(f"Rate limit for {model_name} (attempt {attempt}/{MAX_RETRIES})")
            else:
                logger.warning(f"API error from {model_name} (attempt {attempt}/{MAX_RETRIES}): {exc}")
        except Exception as exc:
            logger.exception(f"Unexpected error calling {model_name} (attempt {attempt}/{MAX_RETRIES}): {exc}")

        if attempt < MAX_RETRIES:
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.info(f"Retrying {model_name} in {delay}s...")
            await asyncio.sleep(delay)

    logger.error(f"All {MAX_RETRIES} attempts failed for {model_name}")
    return ""


async def _try_free_text_models(prompt: str, timeout: float = 10.0) -> str:
    """Try free models from all providers when credits/rate limits are hit."""
    for model in FREE_TEXT_MODELS:
        try:
            model_client = _get_client_for_model(model)
            if model_client is None:
                continue
            response = await asyncio.wait_for(
                model_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                ),
                timeout=timeout
            )
            result = response.choices[0].message.content
            if result:
                logger.info(f"Free fallback model {model} succeeded")
                return result
        except Exception as exc:
            logger.warning(f"Free fallback {model} failed: {exc}")
            continue
    return ""


class AllModelsFailedError(Exception):
    """Raised when all models in the racing pool fail to produce a response."""
    pass


async def get_ai_response_concurrently(prompt: str, timeout: float = 10.0) -> str:
    """Race multiple AI models across providers and return the first successful response."""
    tasks = [asyncio.create_task(ask_ai(prompt, m, timeout)) for m in MODELS_POOL]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in done:
        result = task.result()
        if result:
            for p in pending:
                p.cancel()
            if pending:
                await asyncio.wait(pending, timeout=2)
            return result

    if pending:
        done_next, _ = await asyncio.wait(pending, timeout=5)
        for task in done_next:
            result = task.result()
            if result:
                return result

    raise AllModelsFailedError("All grading models failed to produce a response after retries")


# ---------------------------------------------------------------------------
# Image grading
# ---------------------------------------------------------------------------
async def grade_image(image_base64: str, subject: str) -> str:
    """Grade an image-based assignment using GPT-4o vision."""
    response = await client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": f"Subject: {subject}\n{VISION_PROMPT}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }]
    )
    return response.choices[0].message.content


async def grade_image_with_markup(image_base64: str, subject: str) -> str:
    """Grade an image assignment and return structured markup JSON.

    Tries GPT-4o first, then falls back to free vision-capable models
    across all configured providers.
    """
    marking_prompt = SUBJECT_PROMPTS.get(subject, GENERIC_MARKING_PROMPT)
    full_prompt = f"Subject: {subject}\n\n{marking_prompt}\n\n{JSON_SCHEMA_PROMPT}"

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": full_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]
    }]

    models_to_try = ["openai/gpt-4o"] + FREE_IMAGE_MODELS

    for model in models_to_try:
        try:
            model_client = _get_client_for_model(model)
            if model_client is None:
                continue
            kwargs = dict(model=model, messages=messages, max_tokens=600)
            if model == "openai/gpt-4o":
                kwargs["response_format"] = {"type": "json_object"}
            response = await model_client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if content:
                clean = _extract_json(content)
                logger.info(f"Image grading succeeded with {model}")
                return clean
        except Exception as exc:
            if _is_credit_error(exc) and model == "openai/gpt-4o":
                logger.warning("gpt-4o credits exhausted, falling back to free image models...")
                continue
            logger.warning(f"Image grading with {model} failed: {exc}")
            continue

    raise RuntimeError("No AI model available for image grading — all providers exhausted")


# ---------------------------------------------------------------------------
# Text assignment judging
# ---------------------------------------------------------------------------
async def judge_assignment(content: str, rubric: str) -> str:
    """Grade a text-based assignment using multi-provider model racing."""
    prompt = f"You are a strict teacher grading a student assignment.\n\nUse this rubric:\n{rubric}\n\nStudent work:\n{content}\n\nReturn:\n- short overall feedback\n- a clear grade in the form X/10\n- concise corrections if needed"
    return await get_ai_response_concurrently(prompt, timeout=12.0)