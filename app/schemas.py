import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DeliveryOptions(BaseModel):
    strategy: Optional[str] = "high_reliability"
    channels: Optional[List[str]] = None

class NotificationRequest(BaseModel):
    trace_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="ID"
    )
    user_id: str = Field(..., description="Внутренний ID пользователя")
    event_name: str = Field(..., description="Событие (н-р, 'order.shipped')")
    payload: Dict[str, Any] = Field(..., description="Данные для шаблона")
    delivery_options: Optional[DeliveryOptions] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid-12345",
                "event_name": "order.shipped",
                "payload": {
                    "customer_name": "Иван",
                    "order_id": 5001,
                    "tracking_number": "ZN123456789"
                }
            }
        }

class NotificationResponse(BaseModel):
    status: str = "queued"
    message: str = "Notification task accepted and queued for processing."
    notification_id: uuid.UUID = Field(..., description="ID задачи")