"""
Tests for nitro.tasks — background task queue module.

Covers: TaskStatus, TaskResult, TaskMessage, MemoryTaskQueue,
        Worker (execution, retries, concurrency), @task decorator,
        TaskProxy (delay, apply_async, bind).
"""

import asyncio
import time

import pytest

from nitro.tasks import (
    MemoryTaskQueue,
    TaskMessage,
    TaskProxy,
    TaskQueueInterface,
    TaskResult,
    TaskStatus,
    Worker,
    generate_task_id,
    task,
)


# ---------------------------------------------------------------------------
# TaskStatus enum
# ---------------------------------------------------------------------------


class TestTaskStatus:
    def test_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.RETRYING.value == "retrying"

    def test_all_statuses_exist(self):
        assert len(TaskStatus) == 6


# ---------------------------------------------------------------------------
# TaskResult dataclass
# ---------------------------------------------------------------------------


class TestTaskResult:
    def test_basic_creation(self):
        r = TaskResult(task_id="abc", name="my.task", status=TaskStatus.COMPLETED)
        assert r.task_id == "abc"
        assert r.name == "my.task"
        assert r.status == TaskStatus.COMPLETED
        assert r.result is None
        assert r.error is None

    def test_duration_when_timed(self):
        r = TaskResult(
            task_id="t1",
            name="t",
            status=TaskStatus.COMPLETED,
            started_at=100.0,
            finished_at=102.5,
        )
        assert r.duration == pytest.approx(2.5)

    def test_duration_none_when_not_started(self):
        r = TaskResult(task_id="t1", name="t", status=TaskStatus.PENDING)
        assert r.duration is None

    def test_is_done_for_terminal_states(self):
        for status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            r = TaskResult(task_id="t1", name="t", status=status)
            assert r.is_done is True

    def test_is_done_false_for_active_states(self):
        for status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING):
            r = TaskResult(task_id="t1", name="t", status=status)
            assert r.is_done is False

    def test_result_value(self):
        r = TaskResult(
            task_id="t1",
            name="t",
            status=TaskStatus.COMPLETED,
            result={"key": "value"},
        )
        assert r.result == {"key": "value"}

    def test_error_message(self):
        r = TaskResult(
            task_id="t1",
            name="t",
            status=TaskStatus.FAILED,
            error="ValueError: bad input",
        )
        assert r.error == "ValueError: bad input"


# ---------------------------------------------------------------------------
# TaskMessage dataclass
# ---------------------------------------------------------------------------


class TestTaskMessage:
    def test_defaults(self):
        msg = TaskMessage(task_id="m1", name="process")
        assert msg.args == ()
        assert msg.kwargs == {}
        assert msg.max_retries == 0
        assert msg.retry_count == 0
        assert msg.eta is None
        assert msg.created_at > 0

    def test_with_args_and_kwargs(self):
        msg = TaskMessage(
            task_id="m2",
            name="send_email",
            args=("user@example.com",),
            kwargs={"subject": "Hi"},
            max_retries=3,
        )
        assert msg.args == ("user@example.com",)
        assert msg.kwargs == {"subject": "Hi"}
        assert msg.max_retries == 3


# ---------------------------------------------------------------------------
# generate_task_id
# ---------------------------------------------------------------------------


class TestGenerateTaskId:
    def test_returns_string(self):
        tid = generate_task_id()
        assert isinstance(tid, str)

    def test_length_is_12(self):
        tid = generate_task_id()
        assert len(tid) == 12

    def test_unique(self):
        ids = {generate_task_id() for _ in range(100)}
        assert len(ids) == 100


# ---------------------------------------------------------------------------
# TaskQueueInterface ABC
# ---------------------------------------------------------------------------


class TestTaskQueueInterface:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            TaskQueueInterface()


# ---------------------------------------------------------------------------
# MemoryTaskQueue — enqueue / dequeue
# ---------------------------------------------------------------------------


class TestMemoryQueueEnqueueDequeue:
    @pytest.mark.asyncio
    async def test_enqueue_and_dequeue(self):
        q = MemoryTaskQueue()
        msg = TaskMessage(task_id="t1", name="job")
        tid = await q.enqueue(msg)
        assert tid == "t1"
        out = await q.dequeue(timeout=1.0)
        assert out is not None
        assert out.task_id == "t1"
        assert out.name == "job"

    @pytest.mark.asyncio
    async def test_dequeue_timeout_returns_none(self):
        q = MemoryTaskQueue()
        result = await q.dequeue(timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_fifo_order(self):
        q = MemoryTaskQueue()
        await q.enqueue(TaskMessage(task_id="a", name="first"))
        await q.enqueue(TaskMessage(task_id="b", name="second"))
        first = await q.dequeue(timeout=1.0)
        second = await q.dequeue(timeout=1.0)
        assert first.task_id == "a"
        assert second.task_id == "b"

    @pytest.mark.asyncio
    async def test_size(self):
        q = MemoryTaskQueue()
        assert await q.size() == 0
        await q.enqueue(TaskMessage(task_id="t1", name="j"))
        await q.enqueue(TaskMessage(task_id="t2", name="j"))
        assert await q.size() == 2


# ---------------------------------------------------------------------------
# MemoryTaskQueue — cancel
# ---------------------------------------------------------------------------


class TestMemoryQueueCancel:
    @pytest.mark.asyncio
    async def test_cancel_pending(self):
        q = MemoryTaskQueue()
        await q.enqueue(TaskMessage(task_id="t1", name="job"))
        assert await q.cancel("t1") is True
        result = await q.get_result("t1")
        assert result is not None
        assert result.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self):
        q = MemoryTaskQueue()
        assert await q.cancel("nope") is False

    @pytest.mark.asyncio
    async def test_cancelled_task_skipped_on_dequeue(self):
        q = MemoryTaskQueue()
        await q.enqueue(TaskMessage(task_id="t1", name="skip"))
        await q.enqueue(TaskMessage(task_id="t2", name="keep"))
        await q.cancel("t1")
        out = await q.dequeue(timeout=1.0)
        assert out.task_id == "t2"


# ---------------------------------------------------------------------------
# MemoryTaskQueue — clear
# ---------------------------------------------------------------------------


class TestMemoryQueueClear:
    @pytest.mark.asyncio
    async def test_clear_removes_all(self):
        q = MemoryTaskQueue()
        await q.enqueue(TaskMessage(task_id="t1", name="j"))
        await q.enqueue(TaskMessage(task_id="t2", name="j"))
        removed = await q.clear()
        assert removed == 2
        assert await q.size() == 0

    @pytest.mark.asyncio
    async def test_clear_empty_queue(self):
        q = MemoryTaskQueue()
        assert await q.clear() == 0


# ---------------------------------------------------------------------------
# MemoryTaskQueue — results
# ---------------------------------------------------------------------------


class TestMemoryQueueResults:
    @pytest.mark.asyncio
    async def test_store_and_get_result(self):
        q = MemoryTaskQueue()
        r = TaskResult(task_id="t1", name="j", status=TaskStatus.COMPLETED, result=42)
        await q.store_result(r)
        fetched = await q.get_result("t1")
        assert fetched is not None
        assert fetched.result == 42

    @pytest.mark.asyncio
    async def test_get_missing_result(self):
        q = MemoryTaskQueue()
        assert await q.get_result("nope") is None

    @pytest.mark.asyncio
    async def test_list_results(self):
        q = MemoryTaskQueue()
        for i in range(5):
            await q.store_result(
                TaskResult(
                    task_id=f"t{i}",
                    name="j",
                    status=TaskStatus.COMPLETED,
                    finished_at=time.time(),
                )
            )
        results = await q.list_results(limit=3)
        assert len(results) == 3
        # Most recent first
        assert results[0].task_id == "t4"

    @pytest.mark.asyncio
    async def test_list_pending(self):
        q = MemoryTaskQueue()
        await q.enqueue(TaskMessage(task_id="t1", name="j"))
        await q.enqueue(TaskMessage(task_id="t2", name="j"))
        pending = await q.list_pending()
        assert len(pending) == 2


# ---------------------------------------------------------------------------
# Worker — registration
# ---------------------------------------------------------------------------


class TestWorkerRegistration:
    def test_register_and_lookup(self):
        q = MemoryTaskQueue()
        w = Worker(q)

        def my_func():
            pass

        w.register("my.task", my_func)
        assert w.get_registered("my.task") is my_func

    def test_lookup_missing(self):
        q = MemoryTaskQueue()
        w = Worker(q)
        assert w.get_registered("nope") is None

    def test_registered_tasks_dict(self):
        q = MemoryTaskQueue()
        w = Worker(q)
        w.register("a", lambda: 1)
        w.register("b", lambda: 2)
        assert set(w.registered_tasks.keys()) == {"a", "b"}


# ---------------------------------------------------------------------------
# Worker — execution
# ---------------------------------------------------------------------------


class TestWorkerExecution:
    @pytest.mark.asyncio
    async def test_processes_sync_task(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)

        def add(a, b):
            return a + b

        w.register("add", add)
        msg = TaskMessage(task_id="t1", name="add", args=(3, 4))
        await q.enqueue(msg)
        await w.start()
        await asyncio.sleep(0.3)
        await w.stop()

        result = await q.get_result("t1")
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == 7
        assert result.duration is not None
        assert result.duration >= 0

    @pytest.mark.asyncio
    async def test_processes_async_task(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)

        async def async_add(a, b):
            await asyncio.sleep(0.01)
            return a + b

        w.register("async_add", async_add)
        msg = TaskMessage(task_id="t1", name="async_add", args=(10, 20))
        await q.enqueue(msg)
        await w.start()
        await asyncio.sleep(0.3)
        await w.stop()

        result = await q.get_result("t1")
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == 30

    @pytest.mark.asyncio
    async def test_handles_task_failure(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)

        def fail():
            raise ValueError("boom")

        w.register("fail", fail)
        msg = TaskMessage(task_id="t1", name="fail")
        await q.enqueue(msg)
        await w.start()
        await asyncio.sleep(0.3)
        await w.stop()

        result = await q.get_result("t1")
        assert result is not None
        assert result.status == TaskStatus.FAILED
        assert "ValueError: boom" in result.error

    @pytest.mark.asyncio
    async def test_unregistered_task_fails(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)
        msg = TaskMessage(task_id="t1", name="unknown.task")
        await q.enqueue(msg)
        await w.start()
        await asyncio.sleep(0.3)
        await w.stop()

        result = await q.get_result("t1")
        assert result is not None
        assert result.status == TaskStatus.FAILED
        assert "No handler registered" in result.error


# ---------------------------------------------------------------------------
# Worker — retries
# ---------------------------------------------------------------------------


class TestWorkerRetries:
    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("not yet")
            return "ok"

        w.register("flaky", flaky)
        msg = TaskMessage(task_id="t1", name="flaky", max_retries=3)
        await q.enqueue(msg)
        await w.start()
        await asyncio.sleep(1.0)
        await w.stop()

        result = await q.get_result("t1")
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausted_retries_fail(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)

        def always_fail():
            raise RuntimeError("permanent")

        w.register("always_fail", always_fail)
        msg = TaskMessage(task_id="t1", name="always_fail", max_retries=2)
        await q.enqueue(msg)
        await w.start()
        await asyncio.sleep(1.0)
        await w.stop()

        result = await q.get_result("t1")
        assert result is not None
        assert result.status == TaskStatus.FAILED
        assert result.retries == 2


# ---------------------------------------------------------------------------
# Worker — lifecycle
# ---------------------------------------------------------------------------


class TestWorkerLifecycle:
    @pytest.mark.asyncio
    async def test_start_stop(self):
        q = MemoryTaskQueue()
        w = Worker(q)
        assert w.is_running is False
        await w.start()
        assert w.is_running is True
        await w.stop()
        assert w.is_running is False

    @pytest.mark.asyncio
    async def test_double_start_is_noop(self):
        q = MemoryTaskQueue()
        w = Worker(q)
        await w.start()
        await w.start()  # Should not raise
        assert w.is_running is True
        await w.stop()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_tasks(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=4, poll_interval=0.05)
        results_order = []

        async def slow_task(task_num):
            await asyncio.sleep(0.05)
            results_order.append(task_num)
            return task_num

        w.register("slow", slow_task)
        for i in range(4):
            await q.enqueue(
                TaskMessage(task_id=f"t{i}", name="slow", args=(i,))
            )

        await w.start()
        await asyncio.sleep(0.5)
        await w.stop()

        # All 4 should have completed
        for i in range(4):
            r = await q.get_result(f"t{i}")
            assert r is not None
            assert r.status == TaskStatus.COMPLETED
            assert r.result == i


# ---------------------------------------------------------------------------
# @task decorator
# ---------------------------------------------------------------------------


class TestTaskDecorator:
    def test_without_parentheses(self):
        @task
        def my_task(x):
            return x * 2

        assert isinstance(my_task, TaskProxy)
        assert my_task.name.endswith("my_task")
        assert my_task(5) == 10  # direct call works

    def test_with_parentheses(self):
        @task(max_retries=3)
        def my_task(x):
            return x + 1

        assert isinstance(my_task, TaskProxy)
        assert my_task.max_retries == 3
        assert my_task(5) == 6

    def test_custom_name(self):
        @task(name="custom.name")
        def my_task():
            pass

        assert my_task.name == "custom.name"

    def test_preserves_function_name(self):
        @task
        def send_email():
            pass

        assert send_email.__name__ == "send_email"

    def test_async_function(self):
        @task
        async def async_job():
            return 42

        assert isinstance(async_job, TaskProxy)
        loop = asyncio.new_event_loop()
        try:
            assert loop.run_until_complete(async_job()) == 42
        finally:
            loop.close()


# ---------------------------------------------------------------------------
# TaskProxy — delay / apply_async
# ---------------------------------------------------------------------------


class TestTaskProxy:
    @pytest.mark.asyncio
    async def test_delay_without_bind_raises(self):
        @task
        def my_task():
            pass

        with pytest.raises(RuntimeError, match="not bound"):
            await my_task.delay()

    @pytest.mark.asyncio
    async def test_delay_enqueues(self):
        q = MemoryTaskQueue()

        @task
        def add(a, b):
            return a + b

        add.bind(q)
        tid = await add.delay(1, 2)
        assert isinstance(tid, str)
        assert len(tid) == 12
        assert await q.size() == 1

    @pytest.mark.asyncio
    async def test_apply_async_with_countdown(self):
        q = MemoryTaskQueue()

        @task
        def my_task():
            pass

        my_task.bind(q)
        before = time.time()
        await my_task.apply_async(countdown=10.0)
        msg = await q.dequeue(timeout=0.1)
        # Task should have ETA ~10s in the future, so dequeue should skip it
        # and return None (the message goes back in the queue)
        assert msg is None

    @pytest.mark.asyncio
    async def test_apply_async_custom_task_id(self):
        q = MemoryTaskQueue()

        @task
        def my_task():
            pass

        my_task.bind(q)
        tid = await my_task.apply_async(task_id="custom-id-123")
        assert tid == "custom-id-123"

    @pytest.mark.asyncio
    async def test_apply_async_with_retries_override(self):
        q = MemoryTaskQueue()

        @task(max_retries=1)
        def my_task():
            pass

        my_task.bind(q)
        await my_task.apply_async(max_retries=5)
        msg = await q.dequeue(timeout=1.0)
        assert msg.max_retries == 5

    @pytest.mark.asyncio
    async def test_bind_returns_self(self):
        q = MemoryTaskQueue()

        @task
        def my_task():
            pass

        result = my_task.bind(q)
        assert result is my_task


# ---------------------------------------------------------------------------
# Integration — @task + Worker + MemoryTaskQueue
# ---------------------------------------------------------------------------


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_roundtrip(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)

        @task(max_retries=1)
        def multiply(a, b):
            return a * b

        multiply.bind(q)
        w.register(multiply.name, multiply.func)

        tid = await multiply.delay(6, 7)
        await w.start()
        await asyncio.sleep(0.3)
        await w.stop()

        result = await q.get_result(tid)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == 42

    @pytest.mark.asyncio
    async def test_async_task_roundtrip(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)

        @task
        async def greet(name):
            return f"Hello, {name}!"

        greet.bind(q)
        w.register(greet.name, greet.func)

        tid = await greet.delay("Nitro")
        await w.start()
        await asyncio.sleep(0.3)
        await w.stop()

        result = await q.get_result(tid)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "Hello, Nitro!"

    @pytest.mark.asyncio
    async def test_multiple_tasks_different_types(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=2, poll_interval=0.05)

        @task
        def sync_job():
            return "sync"

        @task
        async def async_job():
            return "async"

        for t in (sync_job, async_job):
            t.bind(q)
            w.register(t.name, t.func)

        t1 = await sync_job.delay()
        t2 = await async_job.delay()

        await w.start()
        await asyncio.sleep(0.5)
        await w.stop()

        r1 = await q.get_result(t1)
        r2 = await q.get_result(t2)
        assert r1.result == "sync"
        assert r2.result == "async"

    @pytest.mark.asyncio
    async def test_failed_task_with_retry_then_success(self):
        q = MemoryTaskQueue()
        w = Worker(q, concurrency=1, poll_interval=0.05)
        attempts = 0

        @task(max_retries=2)
        def eventually_works():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise RuntimeError("not yet")
            return "done"

        eventually_works.bind(q)
        w.register(eventually_works.name, eventually_works.func)

        tid = await eventually_works.delay()
        await w.start()
        await asyncio.sleep(1.0)
        await w.stop()

        result = await q.get_result(tid)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "done"
