from typing import List, Tuple
import asyncio
import httpx

from sqlalchemy.orm import Session

from app.models.client import Client
from app.config import settings


class MarketingService:
    def __init__(self, db: Session):
        self.db = db

    def _get_recipients(self, client_ids: List[int] | None) -> List[Client]:
        query = self.db.query(Client).filter(Client.is_active == True)
        if client_ids:
            query = query.filter(Client.id.in_(client_ids))
        return query.all()

    async def _send_telegram_message(self, chat_id: str, text: str) -> bool:
        if not settings.telegram_bot_token:
            return False
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(url, json={"chat_id": chat_id, "text": text})
                return resp.status_code == 200 and resp.json().get("ok", False)
            except Exception:
                return False

    async def _send_sms_message(self, phone: str, text: str) -> bool:
        # Placeholder generic HTTP provider. Expect environment variables to configure
        if not settings.sms_base_url or not settings.sms_api_key:
            return False
        headers = {"Authorization": f"Bearer {settings.sms_api_key}"}
        payload = {"to": phone, "from": settings.sms_from_number, "message": text}
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(settings.sms_base_url.rstrip("/") + "/send", json=payload, headers=headers)
                return 200 <= resp.status_code < 300
            except Exception:
                return False

    async def broadcast(self, message: str, channels: List[str], client_ids: List[int] | None) -> Tuple[int, dict]:
        recipients = self._get_recipients(client_ids)
        total = len(recipients)

        results = {ch: {"attempted": 0, "sent": 0, "failed": 0, "errors": []} for ch in channels}

        tasks: List[asyncio.Task] = []
        task_metadata: List[tuple] = []  # (channel, index)

        for client in recipients:
            if "telegram" in channels and client.telegram_chat_id:
                results["telegram"]["attempted"] += 1
                tasks.append(asyncio.create_task(self._send_telegram_message(client.telegram_chat_id, message)))
                task_metadata.append(("telegram", client.id))
            if "sms" in channels and client.phone:
                results["sms"]["attempted"] += 1
                tasks.append(asyncio.create_task(self._send_sms_message(client.phone, message)))
                task_metadata.append(("sms", client.id))

        if tasks:
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)
            for (channel, client_id), ok in zip(task_metadata, outcomes):
                if isinstance(ok, Exception):
                    results[channel]["failed"] += 1
                    results[channel]["errors"].append(f"client {client_id}: {str(ok)}")
                else:
                    if ok:
                        results[channel]["sent"] += 1
                    else:
                        results[channel]["failed"] += 1
        return total, results

