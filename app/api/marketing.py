from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.marketing import MarketingBroadcastRequest, MarketingBroadcastResponse, ChannelResult
from app.services.marketing_service import MarketingService


router = APIRouter(prefix="/marketing", tags=["Marketing"])


@router.post("/broadcast", response_model=ResponseModel)
async def broadcast_message(
    payload: MarketingBroadcastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = MarketingService(db)
    total, results = await service.broadcast(
        message=payload.message,
        channels=payload.channels,
        client_ids=payload.client_ids,
    )

    response = MarketingBroadcastResponse(
        total_recipients=total,
        results=[
            ChannelResult(
                channel=ch,
                attempted=data["attempted"],
                sent=data["sent"],
                failed=data["failed"],
                errors=data["errors"],
            )
            for ch, data in results.items()
        ],
    )

    return ResponseModel(success=True, data=response, message="Broadcast completed")

