"""Persistent encrypted storage for GitHub access tokens."""

from __future__ import annotations

import base64
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

from cryptography.fernet import Fernet

from src.core.config import DATA_DIR, settings
from src.core.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from .token_manager import TokenRecord


logger = get_logger(__name__)


class EncryptedTokenStore:
    """Encrypts and persists GitHub tokens for learner-specific scopes."""

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        encryption_key: Optional[str] = None,
    ) -> None:
        self.storage_path = storage_path or (DATA_DIR / "skills" / "github_tokens.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(self._derive_key(encryption_key))

    def load_records(self) -> Dict[str, Dict[str, Optional[str]]]:
        """Load and decrypt stored token payloads."""
        if not self.storage_path.exists():
            return {}

        try:
            payload = json.loads(self.storage_path.read_text())
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse token store %s: %s", self.storage_path, exc)
            return {}

        records: Dict[str, Dict[str, Optional[str]]] = {}
        for key, data in payload.items():
            token_cipher = data.get("token")
            if not token_cipher:
                continue
            try:
                token_plain = self._fernet.decrypt(token_cipher.encode()).decode()
            except Exception as exc:  # pragma: no cover - corruption handling
                logger.error("Failed to decrypt token for %s: %s", key, exc)
                continue

            records[key] = {
                "token": token_plain,
                "learner_id": data.get("learner_id"),
                "github_handle": data.get("github_handle"),
                "scopes": data.get("scopes"),
                "expires_at": data.get("expires_at"),
                "last_used_at": data.get("last_used_at"),
            }
        return records

    def save_record(self, key: str, record: "TokenRecord") -> None:
        """Persist (and encrypt) a single token record."""
        records = self._load_raw()
        records[key] = self._serialize_record(record)
        self._write(records)

    def delete_record(self, key: str) -> None:
        records = self._load_raw()
        if key in records:
            del records[key]
            self._write(records)

    def _serialize_record(self, record: "TokenRecord") -> Dict[str, Optional[str]]:
        encrypted_token = self._fernet.encrypt(record.token.encode()).decode()
        return {
            "token": encrypted_token,
            "learner_id": record.learner_id,
            "github_handle": record.github_handle,
            "scopes": record.scopes,
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            "last_used_at": record.last_used_at.isoformat(),
        }

    def _load_raw(self) -> Dict[str, Dict[str, Optional[str]]]:
        if not self.storage_path.exists():
            return {}
        try:
            return json.loads(self.storage_path.read_text())
        except json.JSONDecodeError:
            logger.error("Token store JSON corrupted at %s", self.storage_path)
            return {}

    def _write(self, payload: Dict[str, Dict[str, Optional[str]]]) -> None:
        serialized = json.dumps(payload, indent=2, sort_keys=True)
        self.storage_path.write_text(serialized)

    def _derive_key(self, override: Optional[str]) -> bytes:
        source = (override or settings.github_token_encryption_key or settings.secret_key).encode(
            "utf-8"
        )
        digest = hashlib.sha256(source).digest()
        return base64.urlsafe_b64encode(digest)
