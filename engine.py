import os
import asyncio
import re
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

SUBJECT_DETECTION_PROMPT = """
You are an academic subject classifier.

Choose ONLY one:
Mathematics, English, Science, Programming.

Return ONLY the word.
No explanation.

Assignment:
"""

JSON_SCHEMA_PROMPT = """
You are a HUMAN EXAMINER marking with RED PEN.

YOU MUST BE EXTREMELY DENSE IN ANNOTATIONS.

STRICT RULES:
- Minimum 20–50 marks per page
- No skipped questions
- Multiple annotations per question step
- Real teacher-like marking (very frequent)

Return ONLY valid JSON.

DO NOT include markdown or explanation.

JSON FORMAT:

{
  "grade": "X/10",
  "overall_feedback": "short teacher summary",
  "marks": [
    {
      "type": "tick | cross | correction | comment | praise | margin_note | summary",
      "bbox": [ymin, xmin, ymax, xmax],
      "text": "short handwritten teacher note"
    }
  ]
}

CRITICAL bbox rules:
- MUST be normalized 0–1000
- format: [ymin, xmin, ymax, xmax]

MARKING STYLE:
- ticks for correct steps
- crosses for wrong steps
- corrections for wrong reasoning
- comments for explanations
- margin_note for side notes
- summary only once at bottom

Teacher style:
- VERY strict
- very short handwriting style notes:
  "Wrong", "Good", "Check sign", "Redo", "Correct", "Explain better"
"""

MATH_MARKING_PROMPT = """
You are a strict mathematics teacher.
Mark every step carefully.
Be strict and detailed.
"""

ENGLISH_MARKING_PROMPT = """
You are an English teacher.
Mark grammar, clarity, structure.
Be detailed and strict.
"""

SCIENCE_MARKING_PROMPT = """
You are a science teacher.
Check accuracy and reasoning.
Be strict and precise.
"""

PROGRAMMING_MARKING_PROMPT = """
You are a programming instructor.
Check logic, correctness, structure.
Be strict.
"""

GENERIC_MARKING_PROMPT = """
You are a teacher.
Mark thoroughly and strictly.
"""

SUBJECT_PROMPTS = {
    "Mathematics": MATH_MARKING_PROMPT,
    "English": ENGLISH_MARKING_PROMPT,
    "Science": SCIENCE_MARKING_PROMPT,
    "Programming": PROGRAMMING_MARKING_PROMPT,
}

VISION_PROMPT = """
Analyze the assignment and provide:
Strengths, Mistakes, Suggestions, Final Grade
"""

MODELS_POOL = [
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]

def extract_grade(text: str) -> str:
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

async def detect_subject(content):
    response = await client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        messages=[{
            "role": "user",
            "content": SUBJECT_DETECTION_PROMPT + content
        }],
        temperature=0
    )
    return response.choices[0].message.content.strip()

async def ask_ai(prompt, model_name, timeout=10.0):
    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
        )
        return response.choices[0].message.content
    except Exception:
        return None

async def get_ai_response_concurrently(prompt, timeout=10.0):
    tasks = [
        asyncio.create_task(ask_ai(prompt, m, timeout))
        for m in MODELS_POOL
    ]
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED
    )
    for task in done:
        result = task.result()
        if result:
            for p in pending:
                p.cancel()
            return result
    return "Error: All models failed"

async def grade_image(image_base64, subject):
    response = await client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": f"Subject: {subject}\n{VISION_PROMPT}"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }}
            ]
        }]
    )
    return response.choices[0].message.content

async def grade_image_with_markup(image_base64, subject):
    marking_prompt = SUBJECT_PROMPTS.get(subject, GENERIC_MARKING_PROMPT)

    full_prompt = f"""
Subject: {subject}

You are doing STRICT RED PEN EXAM MARKING.

CRITICAL:
- Mark EVERYTHING visible
- Be extremely dense
- Do NOT skip steps
- Mimic real teacher annotations

{marking_prompt}

{JSON_SCHEMA_PROMPT}
"""

    response = await client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": full_prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }}
            ]
        }],
        max_completion_tokens=1200,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content

async def judge_assignment(content, rubric):
    prompt = f"""
You are a strict teacher grading a student assignment.

Use this rubric:
{rubric}

Student work:
{content}

Return:
- short overall feedback
- a clear grade in the form X/10
- concise corrections if needed
"""
    return await get_ai_response_concurrently(prompt, timeout=10.0)

if __name__ == "__main__":
    asyncio.run(asyncio.sleep(0))