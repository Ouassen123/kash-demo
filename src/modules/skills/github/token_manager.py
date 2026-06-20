"""GitHub token management and rotation utilities."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.core.config import settings
from src.core.logging import get_logger
from .token_store import EncryptedTokenStore

logger = get_logger(__name__)


@dataclass
class TokenRecord:
    token: str
    learner_id: Optional[str]
    github_handle: Optional[str]
    scopes: Optional[str]
    expires_at: Optional[datetime]
    last_used_at: datetime

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at


class GitHubTokenManager:
    """Manages GitHub tokens for learners and shared integrations."""

    def __init__(self, token_store: Optional[EncryptedTokenStore] = None) -> None:
        self._tokens: Dict[str, TokenRecord] = {}
        self._lock = asyncio.Lock()
        self._store = token_store or EncryptedTokenStore()
        self._bootstrap_from_store()

    async def register_token(
        self,
        token: str,
        learner_id: Optional[str] = None,
        github_handle: Optional[str] = None,
        scopes: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> None:
        async with self._lock:
            expires_at = (
                datetime.utcnow() + timedelta(seconds=expires_in)
                if expires_in
                else None
            )
            record = TokenRecord(
                token=token,
                learner_id=learner_id,
                github_handle=github_handle,
                scopes=scopes,
                expires_at=expires_at,
                last_used_at=datetime.utcnow(),
            )
            key = learner_id or "shared"
            self._tokens[key] = record
            self._store.save_record(key, record)
            logger.info(
                "Registered GitHub token for %s (scopes=%s, expires=%s)",
                key,
                scopes,
                expires_at,
            )

    async def get_token(self, learner_id: Optional[str] = None) -> Optional[str]:
        async with self._lock:
            key = learner_id if learner_id in self._tokens else "shared"
            record = self._tokens.get(key)

            if record and record.is_expired():
                logger.warning("GitHub token for %s expired; removing", key)
                del self._tokens[key]
                self._store.delete_record(key)
                record = None

            if record:
                record.last_used_at = datetime.utcnow()
                self._store.save_record(key, record)
                return record.token

            # Fallback to default token from settings
            if settings.github_access_token:
                await self.register_token(settings.github_access_token, learner_id="shared")
                return settings.github_access_token

            logger.error("No GitHub token available for %s", learner_id or "shared")
            return None

    async def refresh_learner_link(self, learner_id: str, new_handle: str) -> None:
        """Update stored metadata when a learner handle changes."""
        async with self._lock:
            record = self._tokens.get(learner_id)
            if not record:
                logger.warning("No token record found for learner %s when refreshing handle", learner_id)
                return

            record.github_handle = new_handle
            record.last_used_at = datetime.utcnow()
            self._store.save_record(learner_id, record)
            logger.info("Refreshed GitHub handle for learner %s -> %s", learner_id, new_handle)

    def to_dict(self) -> Dict[str, Dict[str, Optional[str]]]:
        return {
            key: {
                "learner_id": record.learner_id,
                "github_handle": record.github_handle,
                "scopes": record.scopes,
                "expires_at": record.expires_at.isoformat() if record.expires_at else None,
                "last_used_at": record.last_used_at.isoformat(),
            }
            for key, record in self._tokens.items()
        }

    def _bootstrap_from_store(self) -> None:
        stored = self._store.load_records()
        for key, data in stored.items():
            token = data.get("token")
            if not token:
                continue
            record = TokenRecord(
                token=token,
                learner_id=data.get("learner_id"),
                github_handle=data.get("github_handle"),
                scopes=data.get("scopes"),
                expires_at=self._parse_datetime(data.get("expires_at")),
                last_used_at=self._parse_datetime(data.get("last_used_at")) or datetime.utcnow(),
            )
            self._tokens[key] = record

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            logger.warning("Invalid datetime stored for token record: %s", value)
            return None
