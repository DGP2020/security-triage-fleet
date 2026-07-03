from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class Process(BaseModel):
    name: str

class Actor(BaseModel):
    process: Optional[Process] = None

class Endpoint(BaseModel):
    name: str

class ConnectionInfo(BaseModel):
    direction: Optional[str] = None
    dst_endpoint: Optional[Endpoint] = None

class NetworkActivityData(BaseModel):
    connection_info: Optional[ConnectionInfo] = None

class Product(BaseModel):
    name: str
    vendor_name: str

class Metadata(BaseModel):
    version: str = "1.1.0"
    product: Product
    original_time: Optional[str] = None

class FindingInfo(BaseModel):
    title: str
    desc: str
    types: List[str]

# --- Class 4001: Network Activity ---
class NetworkActivityUnmapped(BaseModel):
    attack_type: Optional[Literal["ROLEPLAY_JAILBREAK", "POISONED_RAG", "ADVERSARIAL_ESCALATION"]] = None
    attack_vector: Optional[str] = None
    expected_failure_mode: Optional[str] = None
    sandbox_id: Optional[str] = None
    execution_trace: Optional[List[str]] = None
    rag_context: Optional[List[str]] = None

class NetworkActivityEvent(BaseModel):
    class_uid: int = 4001
    class_name: str = "Network Activity"
    time: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    severity_id: int = 3
    actor: Optional[Actor] = None
    network_activity: Optional[NetworkActivityData] = None
    unmapped: Optional[NetworkActivityUnmapped] = None
    metadata: Metadata

# --- Class 2004: Detection Finding ---
class ABACheckResults(BaseModel):
    agbom_violation: bool
    execution_loop_detected: bool
    prompt_injection_detected: bool
    semantic_drift_detected: bool

class DetectionFindingUnmapped(BaseModel):
    agent_trust_score: float
    circuit_breaker_recommendation: bool
    aba_check_results: ABACheckResults
    evidence: str

class DetectionFindingEvent(BaseModel):
    class_uid: int = 2004
    class_name: str = "Detection Finding"
    time: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    severity_id: int
    finding: FindingInfo
    actor: Optional[Actor] = None
    unmapped: Optional[DetectionFindingUnmapped] = None
    metadata: Metadata

# --- Class 6003: Remediation Activity ---
class RemediationActivityUnmapped(BaseModel):
    quarantine_status: Literal["QUARANTINED", "FAILED", "SKIPPED"]
    memory_snapshot_preserved: bool = True
    revoked_tools: List[str]
    refactored_code: str
    vulnerability_patched: str
    jit_token_used: str
    jit_token_expired_at: str
    token_invalidated: bool

class RemediationActivityEvent(BaseModel):
    class_uid: int = 6003
    class_name: str = "Remediation Activity"
    time: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    severity_id: int = 4
    finding_uid: str
    unmapped: Optional[RemediationActivityUnmapped] = None
    metadata: Metadata
