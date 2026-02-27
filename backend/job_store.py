"""
In-memory job store for async transcription status.
Jobs are updated by the background transcription task and read by the status endpoint.
"""

import logging
import threading
import time
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class JobStore:
    """Thread-safe in-memory store for transcription job state."""

    def __init__(self, max_age_seconds: int = 3600):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._max_age_seconds = max_age_seconds

    def create(self, status: str = "processing", progress: int = 0, message: str = "") -> str:
        """Create a new job and return its id."""
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id,
                "status": status,
                "progress": progress,
                "message": message,
                "transcript": None,
                "error": None,
                "created_at": time.time(),
            }
        return job_id

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by id, or None if not found."""
        with self._lock:
            return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        transcript: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update job fields. Returns False if job not found."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if status is not None:
                job["status"] = status
            if progress is not None:
                job["progress"] = progress
            if message is not None:
                job["message"] = message
            if transcript is not None:
                job["transcript"] = transcript
            if error is not None:
                job["error"] = error
            # Log progress in terminal so you see activity even when no one polls status
            short_id = job_id[:8] if len(job_id) >= 8 else job_id
            if status in ("completed", "failed"):
                logger.info("Job %s: %s", short_id, status)
            elif (progress is not None or message is not None) and job.get("status") == "processing":
                p = job.get("progress", 0)
                msg = job.get("message", "")
                logger.info("Job %s: %s%% - %s", short_id, p, msg)
            return True

    def cleanup_old(self) -> None:
        """Remove jobs older than max_age_seconds."""
        now = time.time()
        with self._lock:
            to_remove = [
                jid for jid, job in self._jobs.items()
                if now - job["created_at"] > self._max_age_seconds
            ]
            for jid in to_remove:
                del self._jobs[jid]
            if to_remove:
                logger.info("JobStore: cleaned up %d old jobs", len(to_remove))
