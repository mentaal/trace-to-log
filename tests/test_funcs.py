import logging
from typing import Callable

from trace_to_log import make_trace


def make_and_use_adder(trace: Callable):
    @trace("*")
    def adder(x: int, y: int) -> int:
        return x + y

    return adder(1, 2)


def make_and_use_adder_in_class(trace: Callable, with_self: bool):
    tracer = trace("*") if with_self else trace("x", "y")

    class T:
        @tracer
        def adder(self, x: int, y: int) -> int:
            return x + y

    t = T()
    return t.adder(1, 2)


def test_adder(caplog, monkeypatch):
    caplog.set_level(logging.DEBUG)
    monkeypatch.delenv("TRACE_ME", raising=False)
    res = make_and_use_adder(make_trace())
    assert res == 3
    assert len(caplog.records) == 0


def test_enabled_adder(monkeypatch, caplog):
    monkeypatch.setenv("TRACE_ME", "1")
    caplog.set_level(logging.DEBUG)

    # determining when tracing is enabled occurs at the time `trace` is created
    res = make_and_use_adder(make_trace())
    print("\n".join(r.msg for r in caplog.records))
    assert res == 3
    assert len(caplog.records) == 3
    assert "Finished adder, returned:3" == caplog.records[-1].msg


def test_always_on_tracing(caplog):
    caplog.set_level(logging.DEBUG)

    # determining when tracing is enabled occurs at the time `trace` is created
    # note this time that no environment variable is required
    trace = make_trace(
        trace_enable=lambda: True,
    )

    res = make_and_use_adder(trace)
    assert res == 3
    assert len(caplog.records) == 3
    assert "Finished adder, returned:3" == caplog.records[-1].msg
    levels = [r.levelname for r in caplog.records]
    assert all(map(lambda level: level == "DEBUG", levels))


def test_info_trace(caplog):
    caplog.set_level(logging.DEBUG)

    trace = make_trace(
        trace_enable=lambda: True,
        log_level=logging.INFO,
    )

    res = make_and_use_adder(trace)
    assert res == 3
    assert len(caplog.records) == 3
    assert "Finished adder, returned:3" == caplog.records[-1].msg
    levels = [r.levelname for r in caplog.records]
    assert all(map(lambda level: level == "INFO", levels))


def test_class_method_trace_with_self(caplog):
    caplog.set_level(logging.DEBUG)

    trace = make_trace(
        trace_enable=lambda: True,
        log_level=logging.INFO,
    )

    res = make_and_use_adder_in_class(trace, with_self=True)
    assert res == 3
    assert len(caplog.records) == 3
    assert "Finished adder, returned:3" == caplog.records[-1].msg
    levels = [r.levelname for r in caplog.records]
    assert all(map(lambda level: level == "INFO", levels))
    assert "self ::" in caplog.records[0].msg


def test_class_method_trace_with_no_self(caplog):
    caplog.set_level(logging.DEBUG)

    trace = make_trace(
        trace_enable=lambda: True,
        log_level=logging.INFO,
    )

    res = make_and_use_adder_in_class(trace, with_self=False)
    assert res == 3
    assert len(caplog.records) == 3
    assert "Finished adder, returned:3" == caplog.records[-1].msg
    levels = [r.levelname for r in caplog.records]
    assert all(map(lambda level: level == "INFO", levels))
    assert "self ::" not in caplog.records[0].msg


def test_variable_args(caplog):
    caplog.set_level(logging.DEBUG)

    trace = make_trace(
        trace_enable=lambda: True,
    )

    @trace("k", "kwargs")
    def var_args(*args, k, **kwargs):
        return k

    res = var_args(k=4, a=4)

    assert res == 4
    assert len(caplog.records) == 3
    assert "Finished var_args, returned:4" == caplog.records[-1].msg
    assert "k :: " in caplog.records[0].msg
    assert "kwargs :: " in caplog.records[0].msg


def test_arg_conversion(caplog):
    caplog.set_level(logging.DEBUG)

    trace = make_trace(
        trace_enable=lambda: True,
    )

    to_hex = lambda x: format(x, "#010x")  # noqa: E731

    @trace("value", address=to_hex)
    def write_32(address: int, value: int):
        pass

    _ = write_32(0x2000_0000, 12)

    assert len(caplog.records) == 3
    assert "address :: 0x20000000" in caplog.records[0].msg
    assert "value :: 12" in caplog.records[0].msg
