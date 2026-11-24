from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.prompt import Prompt, PromptVersion
from app.schemas.version import PromptVersionRead, PromptVersionSummary

router = APIRouter(prefix="/prompts", tags=["Versions"])


def _get_owned_prompt(db: Session, prompt_id: int, owner_id: int) -> Prompt:
    p = (
        db.query(Prompt)
        .filter(Prompt.id == prompt_id, Prompt.owner_id == owner_id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Prompt not found")
    return p


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionSummary])
def list_versions(
    prompt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_owned_prompt(db, prompt_id, user.id)
    rows = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.desc())
        .all()
    )
    result = []
    for r in rows:
        preview = r.content[:120] + ("..." if len(r.content) > 120 else "")
        result.append(
            PromptVersionSummary(
                version=r.version,
                created_at=r.created_at,
                content_preview=preview,
            )
        )
    return result


@router.get(
    "/{prompt_id}/versions/{version}", response_model=PromptVersionRead
)
def get_version(
    prompt_id: int,
    version: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_owned_prompt(db, prompt_id, user.id)
    v = (
        db.query(PromptVersion)
        .filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == version,
        )
        .first()
    )
    if not v:
        raise HTTPException(404, "Version not found")
    return v


@router.post(
    "/{prompt_id}/versions/{version}/restore",
    response_model=PromptVersionRead,
)
def restore_version(
    prompt_id: int,
    version: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = _get_owned_prompt(db, prompt_id, user.id)
    target = (
        db.query(PromptVersion)
        .filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == version,
        )
        .first()
    )
    if not target:
        raise HTTPException(404, "Version not found")

    # Update current prompt content
    prompt.content = target.content

    # Create a new version representing the restore
    last = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.desc())
        .first()
    )
    new_version = PromptVersion(
        prompt_id=prompt_id,
        version=(last.version + 1) if last else 1,
        content=target.content,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version