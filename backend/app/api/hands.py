from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.session import get_db
from app.models.entities import SavedHand, User

router = APIRouter(prefix="/api/hands", tags=["hands"])


class SaveHandRequest(BaseModel):
    title: str | None = None
    payload: dict


@router.get("")
def list_hands(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = (
        db.query(SavedHand)
        .filter(SavedHand.user_id == user.id)
        .order_by(SavedHand.created_at.desc())
        .all()
    )
    return {"items": [_serialize(row) for row in rows]}


@router.post("")
def save_hand(body: SaveHandRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    steps = (body.payload.get("steps") or []) if isinstance(body.payload, dict) else []
    if not steps:
        raise HTTPException(status_code=400, detail="Deal a hand before saving it.")
    start = steps[0].get("name") if steps else "Opening"
    end = steps[-1].get("name") if steps else "Close"
    title = (body.title or "").strip() or f"{start} → {end}"
    row = SavedHand(user_id=user.id, title=title[:255], payload=json.dumps(body.payload))
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.delete("/{hand_id}")
def delete_hand(hand_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    row = db.query(SavedHand).filter(SavedHand.id == hand_id, SavedHand.user_id == user.id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Hand not found.")
    db.delete(row)
    db.commit()
    return {"ok": True}


def _serialize(row: SavedHand) -> dict:
    try:
        payload = json.loads(row.payload)
    except json.JSONDecodeError:
        payload = {}
    return {
        "id": row.id,
        "title": row.title,
        "payload": payload,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
