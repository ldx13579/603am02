from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Repo
from app.schemas import RepoCreate, RepoResponse, RepoUpdate, YAMLImportRequest

router = APIRouter(prefix="/api/repos", tags=["repos"])


@router.get("", response_model=list[RepoResponse])
def list_repos(db: Session = Depends(get_db)):
    return db.query(Repo).order_by(Repo.created_at.desc()).all()


@router.post("", response_model=RepoResponse, status_code=201)
def create_repo(data: RepoCreate, db: Session = Depends(get_db)):
    repo = Repo(name=data.name, local_path=data.local_path, branch=data.branch)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("/{repo_id}", response_model=RepoResponse)
def get_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.put("/{repo_id}", response_model=RepoResponse)
def update_repo(repo_id: int, data: RepoUpdate, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(repo, key, value)

    db.commit()
    db.refresh(repo)
    return repo


@router.delete("/{repo_id}", status_code=204)
def delete_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    db.delete(repo)
    db.commit()


@router.post("/{repo_id}/validate")
def validate_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    path = Path(repo.local_path)
    if not path.exists():
        return {"valid": False, "error": "Path does not exist"}
    if not (path / ".git").exists() and not path.name.endswith(".git"):
        return {"valid": False, "error": "Not a git repository"}
    return {"valid": True, "error": None}


@router.post("/import-yaml")
def import_from_yaml(data: YAMLImportRequest = None, db: Session = Depends(get_db)):
    settings = get_settings()
    config_path = data.config_path if data and data.config_path else settings.REPOS_YAML_PATH

    path = Path(config_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"YAML config not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    repos_data = config.get("repos", [])
    imported = 0

    for r in repos_data:
        existing = db.query(Repo).filter(Repo.local_path == r["path"]).first()
        if not existing:
            repo = Repo(
                name=r["name"],
                local_path=r["path"],
                branch=r.get("branch", "main"),
            )
            db.add(repo)
            imported += 1

    db.commit()
    return {"imported": imported, "total_in_config": len(repos_data)}
