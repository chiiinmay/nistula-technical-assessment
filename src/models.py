from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid

class SourceChannel(str, Enum):
    whatsapp = "whatsapp"
    booking_com = "booking_com"
    airbnb = "airbnb"
    instagram = "instagram"
    direct = "direct"

class QueryType(str, Enum):
    pre_sales_availability = "pre_sales_availability"
    pre_sales_pricing = "pre_sales_pricing"
    post_sales_checkin = "post_sales_checkin"
    special_request = "special_request"
    complaint = "complaint"
    general_enquiry = "general_enquiry"

class ActionType(str, Enum):
    auto_send = "auto_send"
    agent_review = "agent_review"
    escalate = "escalate"

class InboundMessage(BaseModel):
    source: SourceChannel
    guest_name: str
    message: str
    timestamp: datetime
    booking_ref: Optional[str] = None
    property_id: str

class NormalizedMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: SourceChannel
    guest_name: str
    message_text: str
    timestamp: datetime
    booking_ref: Optional[str] = None
    property_id: str
    query_type: Optional[QueryType] = None

class WebhookResponse(BaseModel):
    message_id: str
    query_type: QueryType
    drafted_reply: str
    confidence_score: float
    action: ActionType
