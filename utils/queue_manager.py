import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, Coroutine

from config import MAX_CONCURRENT_TASKS

logger = logging.getLogger(__name__)


@dataclass
class QueueItem:
    task_fn: Callable[[], Coroutine]
    user_id: int
    description: str = ""


class DownloadQueue:
    """
    Har bir foydalanuvchi uchun alohida navbat.
    Bir vaqtda bitta yuklanish bo'ladi — xotira va trafik tejash uchun.
    """

    def __init__(self):
        self._queues: dict[int, asyncio.Queue] = {}
        self._workers: dict[int, asyncio.Task] = {}
        self.stats: dict[int, dict] = {}   # user_id -> {done, failed}
        self._global_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    def _ensure_worker(self, user_id: int):
        if user_id not in self._workers or self._workers[user_id].done():
            self._workers[user_id] = asyncio.create_task(
                self._worker(user_id)
            )

    async def _worker(self, user_id: int):
        q = self._queues[user_id]
        while True:
            item: QueueItem = await q.get()
            try:
                async with self._global_semaphore:
                    await item.task_fn()
                self.stats.setdefault(user_id, {"done": 0, "failed": 0})
                self.stats[user_id]["done"] += 1
            except Exception as e:
                logger.error(f"Queue task error for user {user_id}: {e}")
                self.stats.setdefault(user_id, {"done": 0, "failed": 0})
                self.stats[user_id]["failed"] += 1
            finally:
                q.task_done()

    async def add(self, user_id: int, task_fn: Callable, description: str = ""):
        if user_id not in self._queues:
            self._queues[user_id] = asyncio.Queue()
        self._ensure_worker(user_id)
        item = QueueItem(task_fn=task_fn, user_id=user_id, description=description)
        await self._queues[user_id].put(item)
        return self._queues[user_id].qsize()

    def queue_size(self, user_id: int) -> int:
        q = self._queues.get(user_id)
        return q.qsize() if q else 0

    async def clear_user_queue(self, user_id: int) -> int:
        """
        Clears only pending tasks for a user queue.
        Running task (if any) is not interrupted.
        Returns number of removed pending items.
        """
        q = self._queues.get(user_id)
        if not q:
            return 0

        removed = 0
        while not q.empty():
            try:
                q.get_nowait()
                q.task_done()
                removed += 1
            except asyncio.QueueEmpty:
                break
        return removed


download_queue = DownloadQueue()
