import asyncio
import time
from app.core.config import settings
from openai import AsyncOpenAI

# Groq is OpenAI-compatible. We just point the SDK to Groq's base URL.
groq_client = (
    AsyncOpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url=settings.GROQ_BASE_URL,
    )
    if settings.GROQ_API_KEY
    else None
)

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
]
DEFAULT_MODEL = "openai/gpt-oss-120b"


async def _call_groq(prompt: str, model: str, max_tokens: int) -> dict:
    if not groq_client:
        raise ValueError("GROQ_API_KEY not set in .env")
    t0 = time.perf_counter()
    resp = await groq_client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=max_tokens,
        temperature=0.7,
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    usage = resp.usage
    return {
        "provider": "groq",
        "model": resp.model,
        "output": resp.choices[0].message.content,
        "latency_ms": latency_ms,
        "tokens": {
            "prompt": usage.prompt_tokens if usage else None,
            "completion": usage.completion_tokens if usage else None,
            "total": usage.total_tokens if usage else None,
        },
    }


async def run_prompt(
    provider: str, model: str, prompt: str, max_tokens: int = 500
) -> dict:
    if provider.lower() != "groq":
        raise ValueError("Only 'groq' provider is currently supported.")
    return await _call_groq(prompt, model, max_tokens)


async def compare_prompt(
    prompt: str,
    providers: list[str],
    model: str = "",
    max_tokens: int = 500,
) -> dict:
    if not providers or len(providers) > 4 or any(p.lower() != "groq" for p in providers):
        raise ValueError("Choose between 1 and 4 supported providers: groq.")

    async def _safe(provider: str):
        try:
            result = await _call_groq(prompt, model, max_tokens)
            return {"ok": True, **result}
        except Exception as e:
            return {
                "ok": False,
                "provider": provider,
                "error": str(e),
            }

    results = await asyncio.gather(*[_safe(p) for p in providers])
    return {"prompt": prompt, "results": results}


async def groq_compare_models(
    prompt: str,
    models: list[str],
    max_tokens: int = 500,
) -> dict:
    if not groq_client:
        raise ValueError("GROQ_API_KEY not set in .env")
    
    async def _safe(model: str):
        try:
            result = await _call_groq(prompt, model, max_tokens)
            return {"ok": True, **result}
        except Exception as e:
            return {
                "ok": False,
                "provider": "groq",
                "model": model,
                "error": str(e),
            }

    results = await asyncio.gather(*[_safe(m) for m in models])
    return {"prompt": prompt, "results": results}


# Kept as the route's public name for compatibility with existing clients.
async def openai_compare_models(prompt: str, models: list[str], max_tokens: int = 500) -> dict:
    if not models or len(models) > 4:
        raise ValueError("Choose between 1 and 4 models.")
    return await groq_compare_models(prompt, models, max_tokens)
