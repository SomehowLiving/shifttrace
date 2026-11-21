"""In-process pub/sub that fans backend state changes out to SSE clients."""
from __future__ import annotations

import asyncio
import json
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[str]] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=500)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[str]) -> None:
        self._subscribers.discard(q)

    def publish(self, topic: str, data: Any | None = None) -> None:
        message = json.dumps({"topic": topic, "data": data}, default=str)
        loop = self._loop
        if loop is None:
            return
        for q in list(self._subscribers):
            try:
                running = asyncio.get_running_loop()
            except RuntimeError:
                running = None
            if running is loop:
                self._offer(q, message)
            else:
                loop.call_soon_threadsafe(self._offer, q, message)

    @staticmethod
    def _offer(q: asyncio.Queue[str], message: str) -> None:
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            pass


bus = EventBus()
