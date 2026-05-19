"""Tests for sage_imap.decorators."""

import sys
import warnings

import pytest

from sage_imap.decorators import (
    _performance_metrics,
    authenticated_required,
    cache_result,
    circuit_breaker,
    clear_performance_metrics,
    connection_required,
    deprecated,
    exception_handler,
    get_performance_metrics,
    log_function_calls,
    mailbox_selection_required,
    performance_monitor,
    rate_limit,
    retry_on_failure,
    validate_parameters,
    validate_types,
)
from sage_imap.exceptions import (
    IMAPAuthenticationError,
    IMAPClientError,
    IMAPConfigurationError,
    IMAPConnectionError,
    IMAPMailboxSelectionError,
)


class _MailboxHost:
    current_selection = "INBOX"

    @mailbox_selection_required
    def op(self):
        return "ok"


class _ConnHost:
    connection = object()
    authenticated = True

    @connection_required
    def conn_op(self):
        return 1

    @authenticated_required
    def auth_op(self):
        return 2


def test_mailbox_selection_required_raises():
    host = _MailboxHost()
    host.current_selection = None
    with pytest.raises(IMAPMailboxSelectionError):
        host.op()


def test_mailbox_selection_required_missing_attr():
    class Host:
        @mailbox_selection_required
        def op(self):
            return 1

    with pytest.raises(IMAPMailboxSelectionError):
        Host().op()


def test_connection_and_auth_required():
    host = _ConnHost()
    assert host.conn_op() == 1
    assert host.auth_op() == 2


def test_connection_required_raises():
    class Host:
        connection = None

        @connection_required
        def op(self):
            pass

    with pytest.raises(IMAPConnectionError):
        Host().op()


def test_authenticated_required_raises():
    class Host:
        authenticated = False

        @authenticated_required
        def op(self):
            pass

    with pytest.raises(IMAPAuthenticationError):
        Host().op()


def test_performance_monitor_stores_metrics():
    clear_performance_metrics()

    @performance_monitor(track_time=True, log_performance=False, track_memory=False)
    def work():
        return 42

    assert work() == 42
    metrics = get_performance_metrics()
    assert any("work" in k for k in metrics)


def test_performance_monitor_on_exception():
    @performance_monitor(track_time=True, log_performance=True)
    def fail():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        fail()


def test_performance_monitor_with_memory(mocker):
    proc = mocker.Mock()
    proc.memory_info.side_effect = [mocker.Mock(rss=1000), mocker.Mock(rss=1500)]
    psutil = mocker.Mock()
    psutil.Process.return_value = proc
    mocker.patch.dict(sys.modules, {"psutil": psutil})

    @performance_monitor(track_memory=True, log_performance=False)
    def work():
        return 1

    assert work() == 1


def test_performance_monitor_memory_read_failure(mocker):
    proc = mocker.Mock()
    proc.memory_info.side_effect = [mocker.Mock(rss=1000), RuntimeError("mem")]
    psutil = mocker.Mock()
    psutil.Process.return_value = proc
    mocker.patch.dict(sys.modules, {"psutil": psutil})

    @performance_monitor(track_memory=True, log_performance=False)
    def work():
        return 1

    assert work() == 1


def test_get_performance_metrics_specific_and_clear():
    clear_performance_metrics()
    key = "tests.test_decorators.specific_fn"
    _performance_metrics[key] = [0.1, 0.2]
    assert get_performance_metrics(key)["call_count"] == 2
    clear_performance_metrics(key)
    assert get_performance_metrics(key) == {}


def test_retry_on_failure_success_after_retry(mocker):
    calls = {"n": 0}

    @retry_on_failure(max_retries=2, delay=0, exponential_backoff=False)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("nope")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 2


def test_retry_on_failure_exhausted():
    @retry_on_failure(max_retries=1, delay=0, exponential_backoff=True)
    def always_fail():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        always_fail()


def test_retry_on_failure_on_retry_callback():
    attempts = []

    def on_retry(n, exc):
        attempts.append((n, exc))

    @retry_on_failure(max_retries=1, delay=0, on_retry=on_retry)
    def flaky():
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        flaky()
    assert len(attempts) == 1


def test_validate_parameters():
    @validate_parameters(x=lambda v: v > 0)
    def fn(x):
        return x

    assert fn(1) == 1
    with pytest.raises(IMAPConfigurationError):
        fn(-1)


def test_validate_parameters_validator_raises():
    def bad(_):
        raise TypeError("bad validator")

    @validate_parameters(x=bad)
    def fn(x):
        return x

    with pytest.raises(IMAPConfigurationError):
        fn(1)


def test_log_function_calls():
    @log_function_calls(log_args=True, log_result=True)
    def fn(a):
        return a + 1

    assert fn(1) == 2


def test_log_function_calls_exception():
    @log_function_calls(log_exceptions=True)
    def fn():
        raise ValueError("e")

    with pytest.raises(ValueError):
        fn()


def test_cache_result_no_ttl():
    calls = {"n": 0}

    @cache_result(ttl=None)
    def add(a, b):
        calls["n"] += 1
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert calls["n"] == 1


def test_cache_result_with_ttl_and_eviction():
    @cache_result(ttl=10, maxsize=1, key_func=lambda x: str(x))
    def double(x):
        return x * 2

    assert double(1) == 2
    info = double.cache_info()
    assert info["size"] == 1
    double.cache_clear()
    assert double(2) == 4


def test_cache_result_ttl_expiry(mocker):
    now = {"t": 1000.0}
    mocker.patch("sage_imap.decorators.time.time", side_effect=lambda: now["t"])

    @cache_result(ttl=1, maxsize=8)
    def fn(x):
        return x

    assert fn(1) == 1
    now["t"] = 1002.0
    assert fn(1) == 1


def test_rate_limit_exceeded():
    @rate_limit(calls=1, period=60)
    def limited():
        return True

    assert limited() is True
    with pytest.raises(IMAPClientError):
        limited()


def test_validate_types():
    @validate_types(name=str)
    def fn(name=None):
        return name

    assert fn(name="a") == "a"
    with pytest.raises(IMAPConfigurationError):
        fn(name=123)


@pytest.mark.skipif(not hasattr(__import__("signal"), "SIGALRM"), reason="SIGALRM")
def test_timeout_decorator():
    from sage_imap.decorators import timeout

    @timeout(2)
    def quick():
        return "done"

    assert quick() == "done"


def test_exception_handler_default():
    @exception_handler(exceptions=ValueError, default_return=0)
    def fn():
        raise ValueError("x")

    assert fn() == 0


def test_exception_handler_reraise():
    @exception_handler(exceptions=ValueError, reraise=True)
    def fn():
        raise ValueError("x")

    with pytest.raises(ValueError):
        fn()


def test_deprecated_emits_warning():
    @deprecated(message="use other", version="2.0")
    def old():
        return 1

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert old() == 1
    assert any(issubclass(x.category, DeprecationWarning) for x in w)


def test_performance_monitor_no_track_time():
    @performance_monitor(track_time=False, log_performance=False)
    def fast():
        return 1

    assert fast() == 1


def test_cache_result_eviction_when_full(mocker):
    now = {"t": 1000.0}
    mocker.patch("sage_imap.decorators.time.time", side_effect=lambda: now["t"])

    @cache_result(ttl=100, maxsize=1)
    def fn(x):
        return x

    assert fn(1) == 1
    now["t"] = 1001.0
    assert fn(2) == 2


def test_circuit_breaker_opens_when_threshold_reached(mocker):
    @circuit_breaker(failure_threshold=1, recovery_timeout=60)
    def unstable():
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        unstable()
    with pytest.raises(IMAPClientError):
        unstable()
