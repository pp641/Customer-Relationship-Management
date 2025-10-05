
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from constants import DisputeType, DisputeStatus, Priority


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}


class DisputeForm(BaseModel):
    type: Optional[DisputeType] = None
    bank: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    description: Optional[str] = None
    cardlastfour: Optional[str] = None
    priority: Optional[Priority] = None


class DisputeData(BaseModel):
    id: str = Field(default_factory=lambda: f"DSP{uuid.uuid4().hex[:8].upper()}")
    type: DisputeType
    amount: float
    date: str
    description: str
    status: DisputeStatus = DisputeStatus.SUBMITTED
    priority: Priority
    bank: str
    cardlastfour: str
    createdAt: str = Field(default_factory=lambda: datetime.now().isoformat())


class ChatResponse(BaseModel):
    response: str
    options: Optional[List[str]] = None
    action: Optional[str] = None
    dispute_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}


class DisputeCreateResponse(BaseModel):
    dispute_id: str
    status: str
    priority: str
    next_steps: List[Dict[str, str]]
    estimated_resolution: str
    bank_contact: str
    created_at: str


class GuidanceResponse(BaseModel):
    dispute_type: str
    guidance_steps: List[Dict[str, str]]
    complaint_template: str
    important_documents: List[str]
    time_limits: Dict[str, str]


class BankInfo(BaseModel):
    name: str
    helpline: str
    dispute_email: Optional[str]
    online_portal: Optional[str]


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]


class DisputeListResponse(BaseModel):
    disputes: List[DisputeData]
    total: int
    summary: Dict[str, Dict[str, int]]


class DisputeDetailResponse(BaseModel):
    dispute: DisputeData
    timeline: List[Dict[str, str]]


class SessionData(BaseModel):
    step: str
    dispute_form: Dict[str, Any]
    context: Dict[str, Any]



class UsersDB(BaseModel):
    full_name: str
    hashed_passowrd: str
    active: bool
    role: str
    email: str
