"""
Tests for nitro.scheduler — periodic task scheduling.

Covers: CronExpr parsing, interval parsing, Scheduler lifecycle,
job registration, execution, pause/resume, history tracking,
and Sanic integration.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nitro.scheduler import (
    CronExpr,
    JobRun,
    JobStatus,
    Scheduler,
    ScheduleEntry,
    every,
    sanic_scheduler,
)
from nitro.scheduler.interval import extract_interval, is_interval_schedule, parse_interval


# ======================================================================
# CronExpr — parsing
# ======================================================================


class TestCronExprParsing:
    """Test cron expression parsing."""

    def test_every_minute(self):
        cron = CronExpr("* * * * *")
        assert 0 in cron._minutes
        assert 59 in cron._minutes

    def test_specific_minute(self):
        cron = CronExpr("30 * * * *")
        assert cron._minutes == {30}

    def test_step_expression(self):
        cron = CronExpr("*/15 * * * *")
        assert cron._minutes == {0, 15, 30, 45}

    def test_range_expression(self):
        cron = CronExpr("* 9-17 * * *")
        assert cron._hours == set(range(9, 18))

    def test_list_expression(self):
        cron = CronExpr("0 9,12,18 * * *")
        assert cron._hours == {9, 12, 18}

    def test_range_with_step(self):
        cron = CronExpr("0-30/10 * * * *")
        assert cron._minutes == {0, 10, 20, 30}

    def test_weekday_expression(self):
        cron = CronExpr("0 9 * * 1-5")
        # 1-5 = Mon-Fri in cron
        assert cron._weekdays == {1, 2, 3, 4, 5}

    def test_complex_expression(self):
        cron = CronExpr("0,30 9-17 1,15 * 1-5")
        assert cron._minutes == {0, 30}
        assert cron._hours == set(range(9, 18))
        assert cron._days == {1, 15}
        assert cron._weekdays == {1, 2, 3, 4, 5}

    def test_invalid_field_count(self):
        with pytest.raises(ValueError, match="5 fields"):
            CronExpr("* * *")

    def test_invalid_field_count_too_many(self):
        with pytest.raises(ValueError, match="5 fields"):
            CronExpr("* * * * * *")

    def test_value_out_of_range(self):
        with pytest.raises(ValueError, match="out of range"):
            CronExpr("60 * * * *")

    def test_negative_step(self):
        with pytest.raises(ValueError):
            CronExpr("*/0 * * * *")

    def test_invalid_range(self):
        with pytest.raises(ValueError, match="Invalid range"):
            CronExpr("30-10 * * * *")

    def test_repr(self):
        cron = CronExpr("*/5 * * * *")
        assert repr(cron) == "CronExpr('*/5 * * * *')"

    def test_equality(self):
        a = CronExpr("*/5 * * * *")
        b = CronExpr("*/5 * * * *")
        assert a == b

    def test_inequality(self):
        a = CronExpr("*/5 * * * *")
        b = CronExpr("*/10 * * * *")
        assert a != b

    def test_hash(self):
        a = CronExpr("*/5 * * * *")
        b = CronExpr("*/5 * * * *")
        assert hash(a) == hash(b)

    def test_expression_property(self):
        cron = CronExpr("0 9 * * 1-5")
        assert cron.expression == "0 9 * * 1-5"


# ======================================================================
# CronExpr — matching
# ======================================================================


class TestCronExprMatching:
    """Test cron expression matching against datetimes."""

    def test_matches_every_minute(self):
        cron = CronExpr("* * * * *")
        dt = datetime(2026, 4, 13, 10, 30, tzinfo=timezone.utc)
        assert cron.matches(dt)

    def test_matches_specific_time(self):
        cron = CronExpr("30 9 * * *")
        # 9:30 should match
        dt = datetime(2026, 4, 13, 9, 30, tzinfo=timezone.utc)
        assert cron.matches(dt)
        # 9:31 should not
        dt2 = datetime(2026, 4, 13, 9, 31, tzinfo=timezone.utc)
        assert not cron.matches(dt2)

    def test_matches_weekday(self):
        cron = CronExpr("0 9 * * 1")  # Monday
        # 2026-04-13 is a Monday
        monday = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        assert monday.weekday() == 0  # Python Monday = 0
        assert cron.matches(monday)

        # 2026-04-14 is Tuesday
        tuesday = datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc)
        assert not cron.matches(tuesday)

    def test_matches_sunday(self):
        cron = CronExpr("0 0 * * 0")  # Sunday in cron
        # 2026-04-12 is a Sunday
        sunday = datetime(2026, 4, 12, 0, 0, tzinfo=timezone.utc)
        assert sunday.weekday() == 6  # Python Sunday = 6
        assert cron.matches(sunday)

    def test_matches_month(self):
        cron = CronExpr("0 0 1 1 *")  # Jan 1st midnight
        jan1 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        assert cron.matches(jan1)
        feb1 = datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc)
        assert not cron.matches(feb1)


# ======================================================================
# CronExpr — next fire time
# ======================================================================


class TestCronExprNextFireTime:
    """Test cron next fire time computation."""

    def test_next_fire_every_minute(self):
        cron = CronExpr("* * * * *")
        now = time.time()
        nxt = cron.next_fire_time(after=now)
        # Should be within the next 60 seconds
        assert nxt > now
        assert nxt <= now + 61

    def test_next_fire_specific_minute(self):
        cron = CronExpr("0 * * * *")
        # If we're at XX:30, next fire should be at XX+1:00
        dt = datetime(2026, 4, 13, 10, 30, 0, tzinfo=timezone.utc)
        nxt = cron.next_fire_time(after=dt.timestamp())
        nxt_dt = datetime.fromtimestamp(nxt, tz=timezone.utc)
        assert nxt_dt.minute == 0
        assert nxt_dt.hour == 11

    def test_next_fire_every_5_minutes(self):
        cron = CronExpr("*/5 * * * *")
        dt = datetime(2026, 4, 13, 10, 7, 0, tzinfo=timezone.utc)
        nxt = cron.next_fire_time(after=dt.timestamp())
        nxt_dt = datetime.fromtimestamp(nxt, tz=timezone.utc)
        assert nxt_dt.minute == 10

    def test_next_fire_advances_past_current(self):
        cron = CronExpr("30 10 * * *")
        # At exactly 10:30, should advance to next day
        dt = datetime(2026, 4, 13, 10, 30, 0, tzinfo=timezone.utc)
        nxt = cron.next_fire_time(after=dt.timestamp())
        nxt_dt = datetime.fromtimestamp(nxt, tz=timezone.utc)
        assert nxt_dt.day == 14
        assert nxt_dt.hour == 10
        assert nxt_dt.minute == 30


# ======================================================================
# Interval parsing
# ======================================================================


class TestIntervalParsing:
    """Test interval expression parsing."""

    def test_seconds(self):
        assert parse_interval("30s") == 30.0

    def test_minutes(self):
        assert parse_interval("5m") == 300.0

    def test_hours(self):
        assert parse_interval("2h") == 7200.0

    def test_days(self):
        assert parse_interval("1d") == 86400.0

    def test_compound(self):
        assert parse_interval("1h30m") == 5400.0

    def test_compound_all(self):
        assert parse_interval("1d2h30m15s") == 95415.0

    def test_bare_number(self):
        assert parse_interval("60") == 60.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_interval("")

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_interval("xyz")

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_interval("0s")

    def test_unknown_unit(self):
        with pytest.raises(ValueError, match="Unknown time unit"):
            parse_interval("5x")


class TestEveryHelper:
    """Test the ``every()`` convenience function."""

    def test_returns_prefixed(self):
        result = every("30s")
        assert result == "@every/30s"

    def test_validates(self):
        with pytest.raises(ValueError):
            every("invalid")

    def test_is_interval_schedule(self):
        assert is_interval_schedule("@every/30s")
        assert not is_interval_schedule("*/5 * * * *")

    def test_extract_interval(self):
        assert extract_interval("@every/5m") == 300.0

    def test_extract_interval_not_interval(self):
        with pytest.raises(ValueError, match="Not an interval"):
            extract_interval("*/5 * * * *")


# ======================================================================
# Base types
# ======================================================================


class TestJobRun:
    """Test JobRun dataclass."""

    def test_duration(self):
        run = JobRun(
            run_id="abc123",
            job_name="test",
            started_at=100.0,
            finished_at=105.0,
        )
        assert run.duration == 5.0

    def test_duration_none(self):
        run = JobRun(run_id="abc123", job_name="test", started_at=100.0)
        assert run.duration is None

    def test_default_success(self):
        run = JobRun(run_id="abc123", job_name="test", started_at=100.0)
        assert run.success is True


class TestScheduleEntry:
    """Test ScheduleEntry dataclass."""

    def test_record_run(self):
        entry = ScheduleEntry(name="test", schedule="* * * * *", func=lambda: None)
        run = JobRun(run_id="r1", job_name="test", started_at=100.0, finished_at=101.0)
        entry.record_run(run)
        assert entry.run_count == 1
        assert entry.error_count == 0
        assert entry.last_run_at == 100.0

    def test_record_failed_run(self):
        entry = ScheduleEntry(name="test", schedule="* * * * *", func=lambda: None)
        run = JobRun(
            run_id="r1", job_name="test", started_at=100.0,
            finished_at=101.0, success=False, error="boom"
        )
        entry.record_run(run)
        assert entry.error_count == 1

    def test_history_trimming(self):
        entry = ScheduleEntry(
            name="test", schedule="* * * * *", func=lambda: None, max_history=3
        )
        for i in range(5):
            run = JobRun(run_id=f"r{i}", job_name="test", started_at=float(i))
            entry.record_run(run)
        assert len(entry.history) == 3
        assert entry.history[0].run_id == "r2"

    def test_last_run(self):
        entry = ScheduleEntry(name="test", schedule="* * * * *", func=lambda: None)
        assert entry.last_run is None
        run = JobRun(run_id="r1", job_name="test", started_at=100.0)
        entry.record_run(run)
        assert entry.last_run is run

    def test_success_rate(self):
        entry = ScheduleEntry(name="test", schedule="* * * * *", func=lambda: None)
        assert entry.success_rate == 1.0
        # 2 success, 1 failure
        for i, ok in enumerate([True, True, False]):
            run = JobRun(
                run_id=f"r{i}", job_name="test", started_at=float(i), success=ok
            )
            entry.record_run(run)
        assert abs(entry.success_rate - 2 / 3) < 0.01


# ======================================================================
# Scheduler — registration
# ======================================================================


class TestSchedulerRegistration:
    """Test job registration."""

    def test_add_interval_job(self):
        s = Scheduler()
        s.add_job("cleanup", every("30s"), lambda: None)
        assert s.job_count == 1
        entry = s.get_job("cleanup")
        assert entry is not None
        assert entry.schedule == "@every/30s"

    def test_add_cron_job(self):
        s = Scheduler()
        s.add_job("report", "*/5 * * * *", lambda: None)
        assert s.job_count == 1

    def test_duplicate_name_raises(self):
        s = Scheduler()
        s.add_job("x", every("1m"), lambda: None)
        with pytest.raises(ValueError, match="already registered"):
            s.add_job("x", every("2m"), lambda: None)

    def test_invalid_cron_raises(self):
        s = Scheduler()
        with pytest.raises(ValueError):
            s.add_job("bad", "not a cron", lambda: None)

    def test_remove_job(self):
        s = Scheduler()
        s.add_job("x", every("1m"), lambda: None)
        assert s.remove_job("x")
        assert s.job_count == 0
        assert not s.remove_job("x")

    def test_list_jobs(self):
        s = Scheduler()
        s.add_job("a", every("1m"), lambda: None)
        s.add_job("b", every("2m"), lambda: None)
        jobs = s.list_jobs()
        assert len(jobs) == 2
        names = {j.name for j in jobs}
        assert names == {"a", "b"}

    def test_decorator_registration(self):
        s = Scheduler()

        @s.job(every("30s"))
        def my_task():
            pass

        assert s.job_count == 1
        entry = s.get_job("my_task")
        assert entry is not None
        assert entry.func is my_task

    def test_decorator_custom_name(self):
        s = Scheduler()

        @s.job(every("1m"), name="custom")
        def my_task():
            pass

        assert s.get_job("custom") is not None
        assert s.get_job("my_task") is None


# ======================================================================
# Scheduler — pause / resume
# ======================================================================


class TestSchedulerPauseResume:
    """Test pause/resume functionality."""

    def test_pause_job(self):
        s = Scheduler()
        s.add_job("x", every("1m"), lambda: None)
        assert s.pause_job("x")
        assert s.get_job("x").status == JobStatus.PAUSED

    def test_resume_job(self):
        s = Scheduler()
        s.add_job("x", every("1m"), lambda: None)
        s.pause_job("x")
        assert s.resume_job("x")
        assert s.get_job("x").status == JobStatus.ACTIVE

    def test_pause_nonexistent(self):
        s = Scheduler()
        assert not s.pause_job("nope")

    def test_resume_nonexistent(self):
        s = Scheduler()
        assert not s.resume_job("nope")


# ======================================================================
# Scheduler — execution
# ======================================================================


class TestSchedulerExecution:
    """Test async job execution."""

    @pytest.mark.asyncio
    async def test_execute_async_job(self):
        s = Scheduler(tick_interval=0.05)
        results = []

        @s.job(every("1s"))
        async def collector():
            results.append(time.time())

        # Force next_run_at to now
        entry = s.get_job("collector")
        entry.next_run_at = time.time() - 1

        await s.start()
        await asyncio.sleep(0.2)
        await s.stop()

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_execute_sync_job(self):
        s = Scheduler(tick_interval=0.05)
        results = []

        @s.job(every("1s"))
        def sync_collector():
            results.append(time.time())

        entry = s.get_job("sync_collector")
        entry.next_run_at = time.time() - 1

        await s.start()
        await asyncio.sleep(0.2)
        await s.stop()

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_failed_job_records_error(self):
        s = Scheduler(tick_interval=0.05)

        @s.job(every("1s"))
        async def broken():
            raise RuntimeError("boom")

        entry = s.get_job("broken")
        entry.next_run_at = time.time() - 1

        await s.start()
        await asyncio.sleep(0.2)
        await s.stop()

        assert entry.error_count >= 1
        assert entry.last_run is not None
        assert not entry.last_run.success
        assert "boom" in entry.last_run.error

    @pytest.mark.asyncio
    async def test_paused_job_not_executed(self):
        s = Scheduler(tick_interval=0.05)
        results = []

        @s.job(every("1s"))
        async def paused_job():
            results.append(1)

        entry = s.get_job("paused_job")
        entry.next_run_at = time.time() - 1
        s.pause_job("paused_job")

        await s.start()
        await asyncio.sleep(0.2)
        await s.stop()

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_job_records_history(self):
        s = Scheduler(tick_interval=0.05)

        @s.job(every("1s"), max_history=5)
        async def tracked():
            return "ok"

        entry = s.get_job("tracked")
        entry.next_run_at = time.time() - 1

        await s.start()
        await asyncio.sleep(0.2)
        await s.stop()

        assert entry.run_count >= 1
        assert len(entry.history) >= 1
        assert entry.history[0].success
        assert entry.history[0].result == "ok"

    @pytest.mark.asyncio
    async def test_next_run_at_advances(self):
        s = Scheduler(tick_interval=0.05)

        @s.job(every("10s"))
        async def advancing():
            pass

        entry = s.get_job("advancing")
        original_next = entry.next_run_at
        entry.next_run_at = time.time() - 1

        await s.start()
        await asyncio.sleep(0.2)
        await s.stop()

        # next_run_at should have advanced
        assert entry.next_run_at > time.time()


# ======================================================================
# Scheduler — lifecycle
# ======================================================================


class TestSchedulerLifecycle:
    """Test start/stop behavior."""

    @pytest.mark.asyncio
    async def test_start_stop(self):
        s = Scheduler()
        assert not s.is_running
        await s.start()
        assert s.is_running
        await s.stop()
        assert not s.is_running

    @pytest.mark.asyncio
    async def test_double_start(self):
        s = Scheduler()
        await s.start()
        await s.start()  # should be idempotent
        assert s.is_running
        await s.stop()

    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        s = Scheduler()
        await s.stop()  # should not raise
        assert not s.is_running


# ======================================================================
# Scheduler — interval scheduling
# ======================================================================


class TestSchedulerIntervalTiming:
    """Test interval-based next_run_at computation."""

    def test_initial_next_run(self):
        s = Scheduler()
        now = time.time()
        s.add_job("x", every("30s"), lambda: None)
        entry = s.get_job("x")
        # Should be ~30s from now
        assert entry.next_run_at is not None
        assert 29 <= entry.next_run_at - now <= 31

    def test_next_run_after_execution(self):
        s = Scheduler()
        s.add_job("x", every("60s"), lambda: None)
        entry = s.get_job("x")
        # Simulate a run
        entry.last_run_at = time.time()
        next_t = s._compute_next_run(entry)
        assert abs(next_t - (entry.last_run_at + 60)) < 1


# ======================================================================
# Sanic integration
# ======================================================================


class TestSanicIntegration:
    """Test Sanic lifecycle hooks."""

    def test_registers_hooks(self):
        mock_app = MagicMock()
        mock_app.name = "TestApp"
        # Sanic decorators need to be callable
        mock_app.before_server_start = MagicMock(side_effect=lambda f: f)
        mock_app.after_server_stop = MagicMock(side_effect=lambda f: f)

        scheduler = Scheduler()
        sanic_scheduler(mock_app, scheduler)

        mock_app.before_server_start.assert_called_once()
        mock_app.after_server_stop.assert_called_once()


# ======================================================================
# Cron weekday translation
# ======================================================================


class TestCronWeekdayTranslation:
    """Test cron-to-Python weekday mapping."""

    def test_sunday_mapping(self):
        # Cron Sunday=0 → Python Sunday=6
        result = CronExpr._translate_weekday({0})
        assert result == {6}

    def test_monday_mapping(self):
        # Cron Monday=1 → Python Monday=0
        result = CronExpr._translate_weekday({1})
        assert result == {0}

    def test_weekday_range(self):
        # Cron Mon-Fri = {1,2,3,4,5} → Python {0,1,2,3,4}
        result = CronExpr._translate_weekday({1, 2, 3, 4, 5})
        assert result == {0, 1, 2, 3, 4}

    def test_all_days(self):
        result = CronExpr._translate_weekday({0, 1, 2, 3, 4, 5, 6})
        assert result == {0, 1, 2, 3, 4, 5, 6}
