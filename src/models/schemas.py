from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Request Models ---
class DateRange(BaseModel):
    start: str = Field(..., description="ISO 8601 start date")
    end: str = Field(..., description="ISO 8601 end date")

class IngestRequest(BaseModel):
    provider_id: str
    range: DateRange
    priority: str = "high"

class ProviderValidationRequest(BaseModel):
    provider_type: str
    api_key: str

# --- Response Models ---
class IngestResponse(BaseModel):
    job_id: str
    status: str
    estimated_completion_ms: int

class JobMetrics(BaseModel):
    records_synced: Optional[int] = 0
    bytes_written: Optional[int] = 0

class JobArtifacts(BaseModel):
    s3_path: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    state: str  # pending, processing, completed, failed
    metrics: Optional[JobMetrics] = None
    artifacts: Optional[JobArtifacts] = None

class LogEntry(BaseModel):
    id: str
    checksum: str
    timestamp: str

class LogListResponse(BaseModel):
    data: List[LogEntry]
    meta: Dict[str, Any]

class ConnectionResponse(BaseModel):
    connection: str
    latency_ms: int

class LogMetadata(BaseModel):
    id: str
    checksum: str
    timestamp: str

class LogSearchResponse(BaseModel):
    data: List[LogMetadata]
    meta: Dict[str, Any]