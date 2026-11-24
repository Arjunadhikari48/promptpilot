from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.prompt import Prompt, PromptVersion
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptRead

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.post("", response_model=PromptRead, status_code=201)
def create_prompt(
    payload: PromptCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = Prompt(**payload.model_dump(), owner_id=user.id)
    db.add(prompt)
    db.flush()
    db.add(PromptVersion(prompt_id=prompt.id, version=1, content=prompt.content))
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("", response_model=list[PromptRead])
def list_prompts(
    q: str | None = Query(None, description="Search in title"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Prompt).filter(Prompt.owner_id == user.id)
    if q:
        query = query.filter(Prompt.title.ilike(f"%{q}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = (
        db.query(Prompt)
        .filter(Prompt.id == prompt_id, Prompt.owner_id == user.id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Prompt not found")
    return p


@router.put("/{prompt_id}", response_model=PromptRead)
def update_prompt(
    prompt_id: int,
    payload: PromptUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = (
        db.query(Prompt)
        .filter(Prompt.id == prompt_id, Prompt.owner_id == user.id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Prompt not found")
    data = payload.model_dump(exclude_unset=True)
    content_changed = "content" in data and data["content"] != p.content
    for k, v in data.items():
        setattr(p, k, v)
    if content_changed:
        last = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == p.id)
            .order_by(PromptVersion.version.desc())
            .first()
        )
        new_version = (last.version + 1) if last else 1
        db.add(PromptVersion(prompt_id=p.id, version=new_version, content=p.content))
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{prompt_id}", status_code=204)
def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = (
        db.query(Prompt)
        .filter(Prompt.id == prompt_id, Prompt.owner_id == user.id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Prompt not found")
    db.delete(p)
    db.commit()
    return None
