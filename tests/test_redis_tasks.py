"""
Tests for nitro.tasks.redis_queue — Redis-backed distributed task queue.

Covers: RedisTaskQueue (enqueue, dequeue, cancel, clear, results,
        list_pending, list_results), serialisation helpers, HAS_REDIS guard.

Uses unittest.mock to simulate Redis — no real Redis server needed.
"""

import json
import sys
import time
from unittest.mock import MagicMock, call, patch

import pytest

from nitro.tasks.base import (
    TaskMessage,
    TaskResult,
    TaskStatus,
    generate_task_id,
)

# Ensure a mock 'redis' module is available before importing the queue,
# since the real redis package may not be installed.
_mock_redis_module = MagicMock()
sys.modules.setdefault("redis", _mock_redis_module)

from nitro.tasks.redis_queue import (  # noqa: E402
    HAS_REDIS,
    RedisTaskQueue,
    _dict_to_task_message,
    _dict_to_task_result,
    _task_message_to_dict,
    _task_result_to_dict,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    """Return a fresh MagicMock Redis client."""
    client = MagicMock()
    # Default returns
    client.llen.return_value = 0
    client.lrange.return_value = []
    client.scan.return_value = (0, [])
    client.sismember.return_value = False
    client.exists.return_value = False
    client.pipeline.return_value = MagicMock()
    client.pipeline.return_value.execute.return_value = []
    return client


@pytest.fixture
def queue(mock_client):
    """Return a RedisTaskQueue with a mocked Redis client."""
    with patch("nitro.tasks.redis_queue._redis_module") as mock_mod:
        mock_mod.from_url.return_value = mock_client
        q = RedisTaskQueue(
            url="redis://localhost:6379/0",
            prefix="test:tasks",
            result_ttl=3600,
        )
    return q


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


class TestSerialisation:
    def test_task_message_roundtrip(self):
        msg = TaskMessage(
            task_id="abc123",
            name="my.task",
            args=(1, "two", 3.0),
            kwargs={"key": "value"},
            max_retries=3,
            retry_count=1,
            created_at=1000.0,
            eta=2000.0,
        )
        d = _task_message_to_dict(msg)
        restored = _dict_to_task_message(d)
        assert restored.task_id == msg.task_id
        assert restored.name == msg.name
        assert restored.args == msg.args
        assert restored.kwargs == msg.kwargs
        assert restored.max_retries == msg.max_retries
        assert restored.retry_count == msg.retry_count
        assert restored.created_at == msg.created_at
        assert restored.eta == msg.eta

    def test_task_message_args_converted_to_list(self):
        msg = TaskMessage(task_id="t1", name="t", args=(1, 2))
        d = _task_message_to_dict(msg)
        assert isinstance(d["args"], list)
        # Restored back to tuple
        restored = _dict_to_task_message(d)
        assert isinstance(restored.args, tuple)

    def test_task_message_defaults(self):
        d = {"task_id": "t1", "name": "test"}
        msg = _dict_to_task_message(d)
        assert msg.args == ()
        assert msg.kwargs == {}
        assert msg.max_retries == 0
        assert msg.retry_count == 0
        assert msg.eta is None

    def test_task_result_roundtrip(self):
        result = TaskResult(
            task_id="r1",
            name="my.task",
            status=TaskStatus.COMPLETED,
            result={"data": [1, 2, 3]},
            error=None,
            created_at=1000.0,
            started_at=1001.0,
            finished_at=1002.5,
            retries=2,
        )
        d = _task_result_to_dict(result)
        restored = _dict_to_task_result(d)
        assert restored.task_id == result.task_id
        assert restored.name == result.name
        assert restored.status == result.status
        assert restored.result == result.result
        assert restored.error == result.error
        assert restored.created_at == result.created_at
        assert restored.started_at == result.started_at
        assert restored.finished_at == result.finished_at
        assert restored.retries == result.retries

    def test_task_result_status_serialised_as_string(self):
        result = TaskResult(task_id="r1", name="t", status=TaskStatus.FAILED)
        d = _task_result_to_dict(result)
        assert d["status"] == "failed"

    def test_task_result_all_statuses_roundtrip(self):
        for status in TaskStatus:
            result = TaskResult(task_id="r1", name="t", status=status)
            d = _task_result_to_dict(result)
            restored = _dict_to_task_result(d)
            assert restored.status == status

    def test_task_message_json_serialisable(self):
        msg = TaskMessage(
            task_id="t1", name="t", args=(1,), kwargs={"a": "b"}
        )
        d = _task_message_to_dict(msg)
        serialised = json.dumps(d)
        assert isinstance(serialised, str)
        assert json.loads(serialised) == d

    def test_task_result_json_serialisable(self):
        result = TaskResult(
            task_id="r1",
            name="t",
            status=TaskStatus.COMPLETED,
            result=42,
        )
        d = _task_result_to_dict(result)
        serialised = json.dumps(d)
        assert isinstance(serialised, str)
        assert json.loads(serialised) == d


# ---------------------------------------------------------------------------
# RedisTaskQueue — construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_import_guard(self):
        with patch("nitro.tasks.redis_queue.HAS_REDIS", False):
            with pytest.raises(ImportError, match="redis package is required"):
                RedisTaskQueue.__init__(
                    MagicMock(spec=RedisTaskQueue),
                    url="redis://localhost",
                )

    def test_default_prefix(self, queue):
        assert queue._prefix == "test:tasks"

    def test_key_helpers(self, queue):
        assert queue._queue_key == "test:tasks:queue"
        assert queue._cancelled_key == "test:tasks:cancelled"
        assert queue._pending_key("abc") == "test:tasks:pending:abc"
        assert queue._result_key("abc") == "test:tasks:result:abc"


# ---------------------------------------------------------------------------
# RedisTaskQueue — enqueue
# ---------------------------------------------------------------------------


class TestEnqueue:
    @pytest.mark.asyncio
    async def test_enqueue_returns_task_id(self, queue, mock_client):
        msg = TaskMessage(task_id="t1", name="job")
        pipe = mock_client.pipeline.return_value
        tid = await queue.enqueue(msg)
        assert tid == "t1"

    @pytest.mark.asyncio
    async def test_enqueue_uses_pipeline(self, queue, mock_client):
        msg = TaskMessage(task_id="t1", name="job", args=(1,))
        pipe = mock_client.pipeline.return_value
        await queue.enqueue(msg)
        mock_client.pipeline.assert_called_once_with(transaction=False)
        # Should set pending key and rpush to queue
        assert pipe.set.called
        assert pipe.rpush.called
        pipe.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_enqueue_stores_correct_data(self, queue, mock_client):
        msg = TaskMessage(
            task_id="t1",
            name="send_email",
            args=("user@test.com",),
            kwargs={"subject": "Hello"},
        )
        pipe = mock_client.pipeline.return_value
        await queue.enqueue(msg)

        # Verify the pending key
        set_call = pipe.set.call_args
        pending_key = set_call[0][0]
        assert pending_key == "test:tasks:pending:t1"

        # Verify the data is valid JSON
        data = json.loads(set_call[0][1])
        assert data["task_id"] == "t1"
        assert data["name"] == "send_email"
        assert data["args"] == ["user@test.com"]
        assert data["kwargs"] == {"subject": "Hello"}


# ---------------------------------------------------------------------------
# RedisTaskQueue — dequeue
# ---------------------------------------------------------------------------


class TestDequeue:
    @pytest.mark.asyncio
    async def test_dequeue_timeout_returns_none(self, queue, mock_client):
        mock_client.blpop.return_value = None
        result = await queue.dequeue(timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_dequeue_returns_message(self, queue, mock_client):
        msg = TaskMessage(task_id="t1", name="job", args=(42,))
        data = json.dumps(_task_message_to_dict(msg))
        mock_client.blpop.return_value = ("test:tasks:queue", data)
        mock_client.sismember.return_value = False

        result = await queue.dequeue(timeout=1.0)
        assert result is not None
        assert result.task_id == "t1"
        assert result.name == "job"
        assert result.args == (42,)

    @pytest.mark.asyncio
    async def test_dequeue_skips_cancelled(self, queue, mock_client):
        msg1 = TaskMessage(task_id="cancelled1", name="skip")
        msg2 = TaskMessage(task_id="t2", name="keep")
        data1 = json.dumps(_task_message_to_dict(msg1))
        data2 = json.dumps(_task_message_to_dict(msg2))

        # First call returns cancelled task, second returns valid task
        mock_client.blpop.side_effect = [
            ("test:tasks:queue", data1),
            ("test:tasks:queue", data2),
        ]
        mock_client.sismember.side_effect = [True, False]

        result = await queue.dequeue(timeout=1.0)
        assert result is not None
        assert result.task_id == "t2"

    @pytest.mark.asyncio
    async def test_dequeue_cleans_pending_key(self, queue, mock_client):
        msg = TaskMessage(task_id="t1", name="job")
        data = json.dumps(_task_message_to_dict(msg))
        mock_client.blpop.return_value = ("test:tasks:queue", data)
        mock_client.sismember.return_value = False

        await queue.dequeue(timeout=1.0)
        mock_client.delete.assert_called_with("test:tasks:pending:t1")


# ---------------------------------------------------------------------------
# RedisTaskQueue — results
# ---------------------------------------------------------------------------


class TestResults:
    @pytest.mark.asyncio
    async def test_store_result_with_ttl(self, queue, mock_client):
        result = TaskResult(
            task_id="t1", name="job", status=TaskStatus.COMPLETED, result=42
        )
        await queue.store_result(result)
        mock_client.setex.assert_called_once()
        key = mock_client.setex.call_args[0][0]
        ttl = mock_client.setex.call_args[0][1]
        assert key == "test:tasks:result:t1"
        assert ttl == 3600

    @pytest.mark.asyncio
    async def test_store_result_without_ttl(self, mock_client):
        with patch("nitro.tasks.redis_queue._redis_module") as mock_mod:
            mock_mod.from_url.return_value = mock_client
            q = RedisTaskQueue(result_ttl=None)

        result = TaskResult(
            task_id="t1", name="job", status=TaskStatus.COMPLETED
        )
        await q.store_result(result)
        mock_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_result_found(self, queue, mock_client):
        stored = TaskResult(
            task_id="t1", name="job", status=TaskStatus.COMPLETED, result=42
        )
        mock_client.get.return_value = json.dumps(_task_result_to_dict(stored))

        result = await queue.get_result("t1")
        assert result is not None
        assert result.task_id == "t1"
        assert result.status == TaskStatus.COMPLETED
        assert result.result == 42

    @pytest.mark.asyncio
    async def test_get_result_not_found(self, queue, mock_client):
        mock_client.get.return_value = None
        result = await queue.get_result("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_result_correct_key(self, queue, mock_client):
        mock_client.get.return_value = None
        await queue.get_result("abc123")
        mock_client.get.assert_called_with("test:tasks:result:abc123")


# ---------------------------------------------------------------------------
# RedisTaskQueue — size
# ---------------------------------------------------------------------------


class TestSize:
    @pytest.mark.asyncio
    async def test_size_returns_llen(self, queue, mock_client):
        mock_client.llen.return_value = 5
        assert await queue.size() == 5
        mock_client.llen.assert_called_with("test:tasks:queue")

    @pytest.mark.asyncio
    async def test_size_empty_queue(self, queue, mock_client):
        mock_client.llen.return_value = 0
        assert await queue.size() == 0


# ---------------------------------------------------------------------------
# RedisTaskQueue — cancel
# ---------------------------------------------------------------------------


class TestCancel:
    @pytest.mark.asyncio
    async def test_cancel_pending_task(self, queue, mock_client):
        mock_client.exists.return_value = True
        pipe = mock_client.pipeline.return_value

        result = await queue.cancel("t1")
        assert result is True

        # Should add to cancelled set and delete pending key
        pipe.sadd.assert_called_with("test:tasks:cancelled", "t1")
        pipe.delete.assert_called_with("test:tasks:pending:t1")

    @pytest.mark.asyncio
    async def test_cancel_stores_result(self, queue, mock_client):
        mock_client.exists.return_value = True

        await queue.cancel("t1")

        # Should store a CANCELLED result
        mock_client.setex.assert_called_once()
        key = mock_client.setex.call_args[0][0]
        data = json.loads(mock_client.setex.call_args[0][2])
        assert key == "test:tasks:result:t1"
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_returns_false(self, queue, mock_client):
        mock_client.exists.return_value = False
        result = await queue.cancel("nope")
        assert result is False


# ---------------------------------------------------------------------------
# RedisTaskQueue — clear
# ---------------------------------------------------------------------------


class TestClear:
    @pytest.mark.asyncio
    async def test_clear_returns_count(self, queue, mock_client):
        mock_client.llen.return_value = 3
        pipe = mock_client.pipeline.return_value

        count = await queue.clear()
        assert count == 3

    @pytest.mark.asyncio
    async def test_clear_deletes_queue_and_cancelled(self, queue, mock_client):
        mock_client.llen.return_value = 0
        pipe = mock_client.pipeline.return_value

        await queue.clear()
        pipe.delete.assert_any_call("test:tasks:queue")
        pipe.delete.assert_any_call("test:tasks:cancelled")

    @pytest.mark.asyncio
    async def test_clear_scans_pending_keys(self, queue, mock_client):
        mock_client.llen.return_value = 2
        # Simulate scan returning some pending keys then done
        mock_client.scan.side_effect = [
            (0, ["test:tasks:pending:t1", "test:tasks:pending:t2"]),
        ]
        pipe = mock_client.pipeline.return_value

        await queue.clear()
        mock_client.delete.assert_called_with(
            "test:tasks:pending:t1", "test:tasks:pending:t2"
        )


# ---------------------------------------------------------------------------
# RedisTaskQueue — list_pending
# ---------------------------------------------------------------------------


class TestListPending:
    @pytest.mark.asyncio
    async def test_list_pending_empty(self, queue, mock_client):
        mock_client.lrange.return_value = []
        pending = await queue.list_pending()
        assert pending == []

    @pytest.mark.asyncio
    async def test_list_pending_returns_messages(self, queue, mock_client):
        msg1 = TaskMessage(task_id="t1", name="job1")
        msg2 = TaskMessage(task_id="t2", name="job2")
        mock_client.lrange.return_value = [
            json.dumps(_task_message_to_dict(msg1)),
            json.dumps(_task_message_to_dict(msg2)),
        ]
        mock_client.sismember.return_value = False

        pending = await queue.list_pending()
        assert len(pending) == 2
        assert pending[0].task_id == "t1"
        assert pending[1].task_id == "t2"

    @pytest.mark.asyncio
    async def test_list_pending_excludes_cancelled(self, queue, mock_client):
        msg1 = TaskMessage(task_id="t1", name="cancelled")
        msg2 = TaskMessage(task_id="t2", name="active")
        mock_client.lrange.return_value = [
            json.dumps(_task_message_to_dict(msg1)),
            json.dumps(_task_message_to_dict(msg2)),
        ]
        mock_client.sismember.side_effect = [True, False]

        pending = await queue.list_pending()
        assert len(pending) == 1
        assert pending[0].task_id == "t2"


# ---------------------------------------------------------------------------
# RedisTaskQueue — list_results
# ---------------------------------------------------------------------------


class TestListResults:
    @pytest.mark.asyncio
    async def test_list_results_empty(self, queue, mock_client):
        mock_client.scan.return_value = (0, [])
        results = await queue.list_results()
        assert results == []

    @pytest.mark.asyncio
    async def test_list_results_sorted_by_finished_at(self, queue, mock_client):
        r1 = TaskResult(
            task_id="t1", name="j", status=TaskStatus.COMPLETED, finished_at=100.0
        )
        r2 = TaskResult(
            task_id="t2", name="j", status=TaskStatus.COMPLETED, finished_at=200.0
        )
        mock_client.scan.return_value = (
            0,
            ["test:tasks:result:t1", "test:tasks:result:t2"],
        )
        mock_client.get.side_effect = [
            json.dumps(_task_result_to_dict(r1)),
            json.dumps(_task_result_to_dict(r2)),
        ]

        results = await queue.list_results()
        assert len(results) == 2
        # Most recent first
        assert results[0].task_id == "t2"
        assert results[1].task_id == "t1"

    @pytest.mark.asyncio
    async def test_list_results_respects_limit(self, queue, mock_client):
        result_data = []
        keys = []
        for i in range(5):
            r = TaskResult(
                task_id=f"t{i}",
                name="j",
                status=TaskStatus.COMPLETED,
                finished_at=float(i),
            )
            result_data.append(json.dumps(_task_result_to_dict(r)))
            keys.append(f"test:tasks:result:t{i}")

        mock_client.scan.return_value = (0, keys)
        mock_client.get.side_effect = result_data

        results = await queue.list_results(limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_list_results_skips_invalid_json(self, queue, mock_client):
        r1 = TaskResult(
            task_id="t1", name="j", status=TaskStatus.COMPLETED, finished_at=100.0
        )
        mock_client.scan.return_value = (
            0,
            ["test:tasks:result:t1", "test:tasks:result:bad"],
        )
        mock_client.get.side_effect = [
            json.dumps(_task_result_to_dict(r1)),
            "not valid json{{{",
        ]

        results = await queue.list_results()
        assert len(results) == 1
        assert results[0].task_id == "t1"
