from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class RunCreate(BaseModel):
    parameter_set_version: int | None = None
    curve_run_id: str | None = None


class RunCreated(BaseModel):
    job_id: str
    run_id: str


class Job(BaseModel):
    id: str
    run_id: str
    portfolio_id: str
    status: JobStatus
    positions_total: int
    positions_done: int
    error_count: int = 0
    errors: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class Run(BaseModel):
    id: str
    portfolio_id: str
    job_id: str
    status: JobStatus
    scenarios: list[str]
    created_at: datetime
    created_by: str | None = None


class PositionResult(BaseModel):
    position_id: str
    name: str
    modelling_class: str
    market_value: float
    scr_interest_up: float
    scr_interest_down: float
    scr_spread: float
    scr_equity: float
    scr_total: float


class RunSummary(BaseModel):
    run_id: str
    portfolio_id: str
    status: JobStatus
    scenarios: list[str]
    positions_total: int
    positions_errored: int
    total_market_value: float
    scr_total: float
    scr_interest_up: float
    scr_interest_down: float
    scr_spread: float
    scr_equity: float
    created_at: datetime


class RunExport(BaseModel):
    download_url: str
    expires_in_minutes: int = 15
