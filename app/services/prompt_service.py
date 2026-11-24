from sqlalchemy.orm import Session
from app.models.prompt import Prompt


def get_prompt_or_none(db: Session, prompt_id: int, owner_id: int) -> Prompt | None:
    return (
        db.query(Prompt)
        .filter(Prompt.id == prompt_id, Prompt.owner_id == owner_id)
        .first()
    )