from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from pydantic import BaseModel
from app.api.auth import get_current_user

router = APIRouter()

class WorkspaceCreate(BaseModel):
    name: str

@router.post("/")
def create_workspace(
    ws: WorkspaceCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_ws = models.Workspace(name=ws.name, user_id=current_user.id)
    db.add(db_ws)
    db.commit()
    db.refresh(db_ws)
    return db_ws

@router.get("/")
def get_workspaces(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Workspace).filter(models.Workspace.user_id == current_user.id).all()

@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id, models.Workspace.user_id == current_user.id).first()
    if db_ws:
        db.delete(db_ws)
        db.commit()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Workspace not found")

class WorkspaceKBUpdate(BaseModel):
    active_kb_dir_ids: list[int]

@router.put("/{workspace_id}/kb-folders")
def update_workspace_kb_folders(
    workspace_id: int,
    payload: WorkspaceKBUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    import json
    db_ws = db.query(models.Workspace).filter(
        models.Workspace.id == workspace_id, 
        models.Workspace.user_id == current_user.id
    ).first()
    if not db_ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    db_ws.active_kb_dir_ids = json.dumps(payload.active_kb_dir_ids)
    db.commit()
    db.refresh(db_ws)
    return db_ws
