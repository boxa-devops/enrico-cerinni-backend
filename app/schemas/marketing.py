from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class MarketingBroadcastRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    channels: List[Literal["sms", "telegram"]] = Field(..., min_items=1)
    client_ids: Optional[List[int]] = Field(None, description="If omitted, send to all active clients")


class ChannelResult(BaseModel):
    channel: Literal["sms", "telegram"]
    attempted: int
    sent: int
    failed: int
    errors: List[str] = Field(default_factory=list)


class MarketingBroadcastResponse(BaseModel):
    total_recipients: int
    results: List[ChannelResult]

