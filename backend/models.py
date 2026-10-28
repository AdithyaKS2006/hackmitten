from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

EventType = Literal["log", "metric", "trace", "change"]
SeverityType = Literal["info", "warn", "error", "critical"]
ConfidenceType = Literal["high", "medium", "low"]
CandidateKind = Literal["service", "change"]
TimelineKind = Literal["change", "anomaly", "log", "metric", "trace"]


class Event(BaseModel):
    id: str
    ts: str
    service: str
    type: EventType
    severity: SeverityType
    name: str
    value: Optional[float] = None
    message: Optional[str] = ""
    raw_ref: Optional[str] = ""
    attrs: dict[str, Any] = Field(default_factory=dict)


class Anomaly(BaseModel):
    id: str
    service: str
    signal: str
    onset_ts: str
    peak_ts: str
    score: float = 0.0
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)


class Candidate(BaseModel):
    rank: int
    kind: CandidateKind
    name: str
    service: str
    score: float = 0.0
    confidence: ConfidenceType
    reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    label: str = "hypothesis"


class TimelineItem(BaseModel):
    ts: str
    service: str
    kind: TimelineKind
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    scenario_id: str
    as_of: Optional[str] = None
    timeline: list[TimelineItem] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)
    unknown: bool = False
    unknown_reason: Optional[str] = None
    graph: dict[str, Any] = Field(default_factory=dict)
    anomalous_services: dict[str, str] = Field(default_factory=dict)
    redaction_sample: dict[str, str] = Field(default_factory=dict)
