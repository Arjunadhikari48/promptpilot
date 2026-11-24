from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.api.deps import get_current_user
from app.services.llm_service import (
    run_prompt,
    compare_prompt,
    openai_compare_models,
)

router = APIRouter(prefix="/llm", tags=["LLM"])


class RunRequest(BaseModel):
    provider: str = Field(default="groq", description="groq")
    model: str | None = None
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=500, ge=1, le=8000)


class CompareRequest(BaseModel):
    prompt: str = Field(min_length=1)
    providers: list[str] = Field(
        default=["groq"],
        description="List of supported providers",
    )
    model: str | None = None
    max_tokens: int = Field(default=500, ge=1, le=8000)


class OpenAIModelsCompareRequest(BaseModel):
    prompt: str = Field(min_length=1)
    models: list[str] = Field(
        default=["openai/gpt-oss-120b", "openai/gpt-oss-20b"],
        description="List of Groq model IDs",
    )
    max_tokens: int = Field(default=500, ge=1, le=8000)


@router.post("/run")
async def run(req: RunRequest, user=Depends(get_current_user)):
    try:
        return await run_prompt(req.provider, req.model or "", req.prompt, req.max_tokens)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(502, "The LLM provider request failed.")


@router.post("/compare")
async def compare(req: CompareRequest, user=Depends(get_current_user)):
    try:
        return await compare_prompt(
            req.prompt, req.providers, req.model or "", req.max_tokens
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(502, "The LLM provider comparison failed.")


@router.post("/openai/compare-models")
async def openai_compare(req: OpenAIModelsCompareRequest, user=Depends(get_current_user)):
    """Compare multiple Groq-hosted models side-by-side (legacy route name)."""
    try:
        return await openai_compare_models(req.prompt, req.models, req.max_tokens)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(502, "The LLM model comparison failed.")
