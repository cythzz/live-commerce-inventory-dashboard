from __future__ import annotations

from pathlib import Path

from src.analytics import generate_excel_report, generate_reports
from src.database import SessionLocal
from src.models import AnalysisJob, JobStatus


def run_analysis_job(job_id: str, report_dir: Path) -> None:
    with SessionLocal() as session:
        job = session.get(AnalysisJob, job_id)
        if job is None:
            return
        job.status = JobStatus.RUNNING
        session.commit()
        try:
            output_path = report_dir / f"analysis-{job.id}.xlsx"
            generate_excel_report(Path(job.sessions_path), Path(job.inventory_path), output_path)
            job.report_path = str(output_path.resolve())
            job.status = JobStatus.SUCCEEDED
            job.error_message = None
        except Exception as exception:  # the failure is persisted for job status queries
            job.status = JobStatus.FAILED
            job.error_message = str(exception)[:2_000]
        session.commit()


def generate_scheduled_local_reports(data_dir: Path, report_dir: Path) -> None:
    generate_reports(data_dir, report_dir)
