"""
nitro.tasks — Background task queue for the Nitro framework.

Provides:
- TaskQueueInterface : Abstract base for queue backends
- MemoryTaskQueue    : In-process queue for dev/testing
- Worker             : Async task processor with configurable concurrency
- task               : Decorator for defining queueable tasks
- TaskProxy          : Wrapper with .delay() and .apply_async()
- TaskStatus         : Task lifecycle states
- TaskResult         : Execution outcome dataclass
- TaskMessage        : Internal queue message

Quick start::

    from nitro.tasks import MemoryTaskQueue, Worker, task

    queue = MemoryTaskQueue()
    worker = Worker(queue, concurrency=2)

    @task(max_retries=3)
    async def send_email(to, subject, body):
        # ... send the email ...
        return {"sent": True}

    # Bind task to queue and register with worker
    send_email.bind(queue)
    worker.register(send_email.name, send_email.func)

    # In your app startup:
    await worker.start()

    # Enqueue work:
    task_id = await send_email.delay("user@example.com", "Hello", "World")

    # Check result later:
    result = await queue.get_result(task_id)

    # Shutdown:
    await worker.stop()

Framework integration (Sanic example)::

    from sanic import Sanic
    from nitro.tasks import MemoryTaskQueue, Worker, task

    app = Sanic("MyApp")
    queue = MemoryTaskQueue()
    worker = Worker(queue)

    @task
    async def process_order(order_id):
        ...

    process_order.bind(queue)
    worker.register(process_order.name, process_order.func)

    @app.before_server_start
    async def start_worker(app, loop):
        await worker.start()

    @app.after_server_stop
    async def stop_worker(app, loop):
        await worker.stop()
"""

from .base import (
    TaskMessage,
    TaskQueueInterface,
    TaskResult,
    TaskStatus,
    generate_task_id,
)
from .decorators import TaskProxy, task
from .memory import MemoryTaskQueue
from .worker import Worker

__all__ = [
    "TaskQueueInterface",
    "MemoryTaskQueue",
    "Worker",
    "task",
    "TaskProxy",
    "TaskStatus",
    "TaskResult",
    "TaskMessage",
    "generate_task_id",
]
