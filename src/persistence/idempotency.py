from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config import get_app_settings
from src.observability.logging import get_logger


class IdempotencyStore:
    def __init__(self) -> None:
        self._logger = get_logger("idempotency-store")
        self._dsn = os.getenv("POSTGRES_DSN", get_app_settings().postgres_dsn)
        self._engine: Optional[AsyncEngine] = None
        self._schema_ready = False
        self._fallback: set[str] = set()

    async def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        self._engine = create_async_engine(self._dsn, pool_pre_ping=True)
        async with self._engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS idempotency_keys (
                        key TEXT PRIMARY KEY,
                        action_id TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL
                    );
                    """
                )
            )
        self._schema_ready = True

    async def claim(self, key: str, action_id: str) -> bool:
        if get_app_settings().demo_mode:
            try:
                await self._ensure_schema()
            except Exception:
                if key in self._fallback:
                    return False
                self._fallback.add(key)
                self._logger.warning("idempotency_fallback_mode_enabled")
                return True
        else:
            await self._ensure_schema()

        assert self._engine is not None
        async with self._engine.begin() as connection:
            result = await connection.execute(
                text(
                    """
                    INSERT INTO idempotency_keys (key, action_id, created_at)
                    VALUES (:key, :action_id, :created_at)
                    ON CONFLICT (key) DO NOTHING;
                    """
                ),
                {"key": key, "action_id": action_id, "created_at": datetime.utcnow()},
            )
        return result.rowcount == 1


idempotency_store = IdempotencyStore()
