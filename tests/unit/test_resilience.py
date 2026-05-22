from __future__ import annotations

import threading
from unittest.mock import Mock

import pytest

from govradar import resilience
from govradar.resilience import SourceCircuitBreakerListener, SourceCircuitBreakerManager

pytestmark = pytest.mark.unit


def test_source_circuit_breaker_manager_reuses_breakers_and_reports_status() -> None:
    manager = SourceCircuitBreakerManager()

    first = manager.get_breaker("정책브리핑")
    second = manager.get_breaker("정책브리핑")
    other = manager.get_breaker("서울시")

    assert first is second
    assert first is not other
    assert manager.get_status() == {
        "정책브리핑": "closed",
        "서울시": "closed",
    }

    manager.reset_breaker("정책브리핑")
    manager.reset_breaker("missing")
    manager.reset_all()
    assert manager.get_status()["정책브리핑"] == "closed"


def test_source_circuit_breaker_manager_is_thread_safe() -> None:
    manager = SourceCircuitBreakerManager()
    breakers = []

    def get_breaker() -> None:
        breakers.append(manager.get_breaker("동시성"))

    threads = [threading.Thread(target=get_breaker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len({id(breaker) for breaker in breakers}) == 1


def test_global_circuit_breaker_manager_singleton(monkeypatch) -> None:
    monkeypatch.setattr(resilience, "_manager", None)

    first = resilience.get_circuit_breaker_manager()
    second = resilience.get_circuit_breaker_manager()

    assert first is second


def test_circuit_breaker_listener_logs_state_failure_and_success(monkeypatch) -> None:
    logger = Mock()
    monkeypatch.setattr(resilience, "logger", logger)
    listener = SourceCircuitBreakerListener()
    cb = Mock(name="breaker")
    cb.name = "정책브리핑"
    old_state = Mock()
    old_state.name = "closed"
    new_state = Mock()
    new_state.name = "open"

    listener.state_change(cb, old_state, new_state)
    listener.state_change(cb, None, new_state)
    listener.before_call(cb, lambda: None)
    listener.failure(cb, RuntimeError("failed"))
    listener.success(cb)

    assert logger.info.call_count == 2
    logger.warning.assert_called_once()
    logger.debug.assert_called_once_with("circuit_breaker_success", source="정책브리핑")
