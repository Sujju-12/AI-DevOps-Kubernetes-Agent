from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ProgressBus:
    queues: dict[str, list[asyncio.Queue]] = field(default_factory=lambda: defaultdict(list))
    history: dict[str, list[dict]] = field(default_factory=lambda: defaultdict(list))

    def subscribe(self, job_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self.queues[job_id].append(queue)
        for event in self.history[job_id]:
            queue.put_nowait(event)
        return queue

    async def publish(self, job_id: str, event: dict) -> None:
        self.history[job_id].append(event)
        for queue in list(self.queues[job_id]):
            await queue.put(event)

    def encode(self, event: dict) -> str:
        name = event.get("event") or "message"
        return f"event: {name}\ndata: {json.dumps(event)}\n\n"


progress_bus = ProgressBus()
