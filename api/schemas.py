from pydantic import BaseModel
from typing import Optional


class RunRequest(BaseModel):
    task: str
    max_steps: int = 15
    repo_dir: Optional[str] = None
    test_cmd: Optional[str] = None
    lint_cmd: Optional[str] = None


class RunInfo(BaseModel):
    run_id: str
    status: str
    task: str
    created_at: str
    log_path: Optional[str] = None
