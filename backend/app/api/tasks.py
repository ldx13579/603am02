from fastapi import APIRouter
from celery.result import AsyncResult

from app.schemas import TaskStatusResponse
from app.tasks.celery_app import celery_app

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    response = TaskStatusResponse(
        task_id=task_id,
        status=result.status,
        progress=None,
        result=None,
        error=None,
    )

    if result.state == "PROGRESS":
        meta = result.info or {}
        response.progress = meta.get("progress", 0)
        response.result = {
            "step": meta.get("step", ""),
            "step_label": meta.get("step_label", ""),
            "step_pct": meta.get("step_pct", 0),
        }
    elif result.state == "SUCCESS":
        response.progress = 100
        response.result = result.result if isinstance(result.result, dict) else {"data": result.result}
    elif result.state == "FAILURE":
        response.error = str(result.info)

    return response
