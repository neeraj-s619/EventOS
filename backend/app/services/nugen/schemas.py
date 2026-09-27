"""
Pydantic Schemas for Nugen Domain-Aligned Event Operations Intelligence.
Enforces strict structured outputs for risk assessment, forecasting,
cascading effects, resource requirements, and data provenance.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class NugenForecast(BaseModel):
    horizon_minutes: int = Field(10, description="Forecast horizon in minutes")
    predicted_occupancy: float = Field(0.0, description="Predicted peak occupancy percentage (0-100)")
    minutes_to_threshold: Optional[float] = Field(None, description="Estimated minutes until safety threshold breach")


class NugenUncertainty(BaseModel):
    lower: Optional[float] = Field(None, description="Lower confidence bound for predicted occupancy")
    upper: Optional[float] = Field(None, description="Upper confidence bound for predicted occupancy")


class NugenDataQuality(BaseModel):
    missing: List[str] = Field(default_factory=list, description="Missing telemetry sensor channels")
    stale: List[str] = Field(default_factory=list, description="Telemetry signals with stale timestamps")
    conflicting: List[str] = Field(default_factory=list, description="Conflicting sensor observations across fused streams")


class NugenModelMetadata(BaseModel):
    model_id: str = Field("nugen-aligned-eventos-v1", description="ID of deployed aligned model")
    base_model: str = Field("nugen-base-v1", description="Base foundation model prior to alignment")
    model_type: str = Field("domain_aligned", description="Model architecture alignment classification")
    customized: bool = Field(True, description="Whether domain customization was executed")
    alignment_name: str = Field("eventos_domain_alignment_v1", description="Identifier of alignment dataset/run")


class NugenActionRecommendation(BaseModel):
    action_id: str = Field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:6].upper()}")
    type: str = Field("divert_crowd", description="Operational action taxonomy type")
    priority: str = Field("HIGH", description="Priority level: LOW, MEDIUM, HIGH, URGENT")
    target_zone: Optional[str] = Field(None, description="Zone targeted for intervention")
    description: str = Field(..., description="Operational action specification for control room")
    estimated_impact: str = Field(..., description="Quantified anticipated result")
    human_approval_required: bool = Field(True, description="Strict human-in-the-loop sign-off gate")


class NugenResourceRequirement(BaseModel):
    resource_type: str = Field(..., description="transport, hospitality, medical, security")
    required_units: int = Field(..., description="Number of additional units needed")
    current_available: int = Field(..., description="Currently reported active provider capacity")
    gap: int = Field(..., description="Unmet capacity deficit")
    urgency: str = Field("IMMEDIATE", description="Fulfillment window: IMMEDIATE, STANDBY, MONITOR")


class NugenOperationalAssessment(BaseModel):
    analysis_id: str = Field(default_factory=lambda: f"NUGEN-{uuid.uuid4().hex[:8].upper()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    mode: str = Field("live", description="Execution mode: live, mock, degraded")
    risk_level: str = Field("NORMAL", description="NORMAL, WATCH, WARNING, CRITICAL, OVERLOAD")
    confidence: float = Field(0.85, ge=0.0, le=1.0, description="Alignment reasoning certainty score")
    summary: str = Field(..., description="Concise operational executive summary (no chain-of-thought)")

    forecast: NugenForecast = Field(default_factory=NugenForecast)
    affected_zones: List[str] = Field(default_factory=list)
    direct_impacts: List[str] = Field(default_factory=list)
    cascading_impacts: List[str] = Field(default_factory=list)

    recommended_actions: List[Dict[str, Any]] = Field(default_factory=list)
    required_resources: List[Dict[str, Any]] = Field(default_factory=list)

    weather_contribution: float = Field(0.0, ge=0.0, le=1.0, description="Proportion of risk driven by weather")
    transport_impact: Dict[str, Any] = Field(default_factory=dict)
    hospitality_impact: Dict[str, Any] = Field(default_factory=dict)

    uncertainty: NugenUncertainty = Field(default_factory=NugenUncertainty)
    human_approval_required: bool = Field(True, description="Whether human operator sign-off is mandatory")
    data_quality: NugenDataQuality = Field(default_factory=NugenDataQuality)
    model_metadata: NugenModelMetadata = Field(default_factory=NugenModelMetadata)

    provenance: Dict[str, Any] = Field(default_factory=dict, description="Audit trace: snapshot IDs, versions, and inputs")


# API Request/Response Schemas
class NugenAnalyzeRequest(BaseModel):
    event_id: Optional[str] = None
    include_cascading: bool = True
    custom_scenario: Optional[Dict[str, Any]] = None


class NugenWhatIfRequest(BaseModel):
    event_id: Optional[str] = None
    scenario_name: str = "moderate_rain"
    precipitation_mm_h: float = 20.0
    wind_speed_kmh: float = 35.0
    temperature_c: float = 24.0
    duration_minutes: int = 45


class NugenStatusResponse(BaseModel):
    configured: bool
    connected: bool
    mode: str  # "live", "mock", "degraded"
    status_label: str
    model_id: str
    base_model: str
    alignment_status: str
    alignment_name: str
    healthy: bool
    total_assessments: int = 0
    last_assessment_at: Optional[str] = None
    latency_ms: Optional[float] = None
    instruction: Optional[str] = None


class NugenAlignmentDatasetItem(BaseModel):
    domain_topic: str
    input_state: Dict[str, Any]
    target_reasoning: Dict[str, Any]
    validation_status: str = "VERIFIED"


class NugenAlignmentManifestResponse(BaseModel):
    alignment_name: str
    base_model: str
    target_model_id: str
    dataset_version: str
    total_domain_examples: int
    categories: List[str]
    training_epochs: int = 3
    target_alignment_score: float = 0.95
    status: str
    dataset_sample: List[Dict[str, Any]]
