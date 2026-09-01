import threading
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass, field


class JobStatus(Enum):
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


@dataclass
class Job:
    id: str
    type: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    result: Any = None
    error: Optional[str] = None
    _cancelled: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def cancel(self):
        with self._lock:
            self._cancelled = True

    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def update_progress(self, value: float):
        with self._lock:
            self.progress = max(0.0, min(1.0, value))


class JobManager:
    def __init__(self, on_event: Optional[Callable[[Job], None]] = None):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._on_event = on_event
        self._workers: List[threading.Thread] = []

    def create(self, job_id: str, job_type: str) -> Job:
        job = Job(id=job_id, type=job_type)
        with self._lock:
            self._jobs[job_id] = job
        self._emit(job)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel(self, job_id: str):
        job = self.get(job_id)
        if job:
            job.cancel()
            job.status = JobStatus.CANCELLED
            self._emit(job)

    def complete(self, job_id: str, result: Any = None):
        job = self.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.result = result
            job.progress = 1.0
            self._emit(job)

    def fail(self, job_id: str, error: str):
        job = self.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = error
            self._emit(job)

    def submit(self, job_id: str, job_type: str, target: Callable, *args, **kwargs):
        job = self.create(job_id, job_type)
        job.status = JobStatus.RUNNING
        self._emit(job)

        def _run():
            try:
                if job.is_cancelled():
                    job.status = JobStatus.CANCELLED
                    self._emit(job)
                    return
                result = target(job, *args, **kwargs)
                if job.is_cancelled():
                    job.status = JobStatus.CANCELLED
                else:
                    job.status = JobStatus.COMPLETED
                    job.result = result
                    job.progress = 1.0
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.error = str(exc)
            self._emit(job)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def _emit(self, job: Job):
        if self._on_event:
            try:
                self._on_event(job)
            except Exception:
                pass
