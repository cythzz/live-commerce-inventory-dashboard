from __future__ import annotations

import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.database import Base, engine, get_db
from src.jobs import generate_scheduled_local_reports, run_analysis_job
from src.models import AnalysisJob, JobStatus


ROOT = Path(__file__).parents[1]
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", ROOT / "uploads"))
REPORT_DIR = Path(os.getenv("REPORT_DIR", ROOT / "reports"))
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if os.getenv("SCHEDULER_ENABLED", "true").lower() == "true" and not scheduler.running:
        scheduler.add_job(
            generate_scheduled_local_reports,
            "cron",
            hour=2,
            args=[ROOT / "data", REPORT_DIR],
            id="daily-local-report",
            replace_existing=True,
        )
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="直播电商数据分析服务",
    version="2.0.0",
    description="上传本地 CSV，后台生成直播场次与库存分析 Excel 报表。",
    lifespan=lifespan,
)


class JobView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: JobStatus
    report_path: str | None
    error_message: str | None


def save_upload(upload: UploadFile, target: Path) -> None:
    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持 CSV 文件")
    with target.open("wb") as output:
        shutil.copyfileobj(upload.file, output)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP"}


@app.post("/api/jobs", response_model=JobView, status_code=202)
def create_job(
    background_tasks: BackgroundTasks,
    sessions: UploadFile = File(...),
    inventory: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AnalysisJob:
    job = AnalysisJob(sessions_path="", inventory_path="")
    db.add(job)
    db.flush()
    job_dir = UPLOAD_DIR / job.id
    job_dir.mkdir(parents=True, exist_ok=False)
    sessions_path = job_dir / "live_sessions.csv"
    inventory_path = job_dir / "inventory.csv"
    save_upload(sessions, sessions_path)
    save_upload(inventory, inventory_path)
    job.sessions_path = str(sessions_path.resolve())
    job.inventory_path = str(inventory_path.resolve())
    db.commit()
    db.refresh(job)
    background_tasks.add_task(run_analysis_job, job.id, REPORT_DIR)
    return job


@app.get("/api/jobs/{job_id}", response_model=JobView)
def get_job(job_id: str, db: Session = Depends(get_db)) -> AnalysisJob:
    job = db.get(AnalysisJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    return job


@app.get("/api/jobs/{job_id}/report")
def download_report(job_id: str, db: Session = Depends(get_db)) -> FileResponse:
    job = db.get(AnalysisJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    if job.status != JobStatus.SUCCEEDED or not job.report_path:
        raise HTTPException(status_code=409, detail="报表尚未生成完成")
    path = Path(job.report_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="报表文件已被清理")
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
