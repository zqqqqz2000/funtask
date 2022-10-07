import asyncio
import time
from multiprocessing import Queue as MltQueue
from queue import Empty
from typing import Dict

from funtask.core.funtask_types import Queue, _T, BreakRef
from funtask.queue.common import NeverBreak


class MultiprocessingQueueFactory:
    def __init__(self):
        self.queues: Dict[str, Queue] = {}

    def factory(self, name: str):
        if name in self.queues:
            return self.queues[name]
        q = MultiprocessingQueue()
        self.queues[name] = q
        return q


class MultiprocessingQueue(Queue):
    def __init__(self):
        self.q = MltQueue()
        self.type = 'multiprocessing'
        self.config = {}

    async def watch_and_get(self, break_ref: BreakRef, timeout: None | float = None) -> _T:
        start_time = time.time()
        while True:
            if timeout and time.time() - start_time >= timeout:
                return None
            try:
                return self.q.get(timeout=0.001, block=True)
            except Empty:
                if break_ref.if_break_now():
                    break
                await asyncio.sleep(0.01)

    async def put(self, obj: _T):
        self.q.put(obj)

    async def get(self, timeout: None | float = None) -> _T:
        return await self.watch_and_get(NeverBreak(), timeout)

    async def qsize(self) -> int:
        return self.q.qsize()

    async def empty(self) -> bool:
        return self.q.empty()
