from fastapi import APIRouter, HTTPException
from app.models.task import TaskConfig
from app.scheduler import add_task, remove_task, scheduler

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/")
async def create_task(task: TaskConfig):
    """Create a new scheduled task"""
    try:
        add_task(task.dict())
        return {"message": f"Task {task.task_id} created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a scheduled task"""
    try:
        remove_task(task_id)
        return {"message": f"Task {task_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_tasks():
    """List all scheduled tasks"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run_time": job.next_run_time,
            "trigger": str(job.trigger)
        })
    return {"tasks": jobs} 