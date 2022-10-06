import asyncio
import uuid

from funtask.core.funtask_types import WorkerManager, Logger, TransTaskMeta
from funtask import Queue, TaskStatus, WorkerStatus, TaskControl
from multiprocessing import Process
import multiprocessing
from typing import Tuple, Any, Dict, Callable

from funtask.core.utils.namespace import with_namespace
from funtask.core.worker import Worker, WorkerQueue

multiprocessing.set_start_method('fork')


class MultiprocessingManager(WorkerManager):
    def __init__(self, logger: Logger):
        self.logger = logger
        # task_uuid -> (process, task_queue, control_queue)
        self.worker2queues: Dict[str, Tuple[Process, Queue, Queue]] = {}

    async def increase_worker(
            self, task_queue_factory: 'Callable[[str], Queue[Tuple[bytes, TransTaskMeta]]]',
            task_status_queue: 'Queue[Tuple[str, str, TaskStatus | WorkerStatus, Any]]',
            control_queue_factory: 'Callable[[str], Queue[Tuple[str, TaskControl]]]', *args, **kwargs
    ) -> str:
        worker_uuid = str(uuid.uuid4())
        task_queue = task_queue_factory(with_namespace('task_queue', worker_uuid))
        control_queue = control_queue_factory(with_namespace('control_queue', worker_uuid))
        worker_runner = Worker(WorkerQueue(
            task_queue=task_queue,
            status_queue=task_status_queue,
            control_queue=control_queue,
        ), worker_uuid, self.logger)
        process = Process(target=lambda: asyncio.run(worker_runner.run()), name=worker_uuid)
        process.start()
        self.worker2queues[worker_uuid] = (process, task_queue, control_queue)
        return worker_uuid

    async def kill_worker(self, worker_uuid: str):
        self.worker2queues[worker_uuid][0].kill()

    async def stop_worker(self, worker_uuid: str):
        ...

    async def get_task_queue(self, worker_uuid: str) -> 'Queue[Tuple[str, TransTaskMeta]]':
        _, task_queue, _ = self.worker2queues[worker_uuid]
        return task_queue

    async def get_control_queue(self, worker_uuid: str) -> 'Queue[Tuple[str, TaskControl]]':
        _, _, control_queue = self.worker2queues[worker_uuid]
        return control_queue
