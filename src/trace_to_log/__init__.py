import logging
import os
import time
from functools import partial, wraps
from inspect import signature
from itertools import starmap
from typing import Any, Callable, Dict, NamedTuple, Optional, Sequence


# ruff: noqa: E731

logger = logging.getLogger(__name__)


class TraceConfig(NamedTuple):
    args_line: Callable = lambda name, value: f"{name} :: {value}"
    entry_func_with_args: Callable = (
        lambda func, args_str: f"Going to call {func.__name__} with args:\n{args_str}"
    )
    entry_func_without_args: Callable = lambda func: f"Going to call {func.__name__}"
    exit_func_without_return_val: Callable = lambda func: f"Finished {func.__name__}"
    exit_func_with_return_val: Callable = (
        lambda func, res: f"Finished {func.__name__}, returned:{res}"
    )
    duration_func: Callable = (
        lambda func, duration: f"{func.__name__} took {duration} seconds"
    )
    trace_enable: Callable = lambda: os.environ.get("TRACE_ME")
    default_str_conversion: Callable = str
    log_level: int = logging.DEBUG


def nop(x: Any) -> Any:
    return x


def make_decorator(
    args_to_log: Sequence[str],
    args_coersion_to_log: Dict[str, Callable],
    trace_return: Optional[Callable],
    trace_config: TraceConfig,
) -> Callable:
    _args_to_log_set = frozenset(args_to_log) | args_coersion_to_log.keys()
    total_args_len = len(args_to_log) + len(args_coersion_to_log)
    if len(_args_to_log_set) != total_args_len:
        raise ValueError("Duplicate args")
    default_str_conversion = trace_config.default_str_conversion
    default_coersion_args = {a: default_str_conversion for a in args_to_log}
    _coersion_args = {**default_coersion_args, **args_coersion_to_log}
    level = trace_config.log_level
    log = partial(logger.log, level)

    def decorator(func: Callable) -> Callable:
        s = signature(func)
        if not _args_to_log_set:
            # log all args
            args_to_log_set = s.parameters.keys()
            coersion_args = {a: default_str_conversion for a in args_to_log_set}
            args_filter = nop
        else:
            args_to_log_set = _args_to_log_set
            coersion_args = _coersion_args
            args_filter = partial(filter, lambda kv: kv[0] in _args_to_log_set)

        typos = args_to_log_set - s.parameters.keys()
        if typos:
            typos_str = ", ".join(typos)
            raise ValueError(
                f"Couldn't find these function parameters. Typo? {typos_str}"
            )

        def get_coerced_kv(k, v):
            return coersion_args[k](v)

        coerced_args_line = lambda k, v: trace_config.args_line(k, get_coerced_kv(k, v))

        @wraps(func)
        def wrapper(*args, **kwargs):
            if args_to_log_set:
                bound_args = s.bind(*args, **kwargs)
                relevant_args = args_filter(bound_args.arguments.items())
                args_str = "\n".join(starmap(coerced_args_line, relevant_args))
                log(trace_config.entry_func_with_args(func, args_str))
            else:
                log(trace_config.entry_func_without_args(func))
            start = time.time()
            try:
                res = func(*args, **kwargs)
            except Exception as e:
                end = time.time()
                elapsed = end - start
                logger.exception(
                    f"exception caught for {func.__name__} after {elapsed} seconds",
                    exc_info=e,
                )
                raise
            end = time.time()
            elapsed = end - start
            duration_func = trace_config.duration_func
            if duration_func:
                log(duration_func(func, elapsed))
            if trace_return:
                converted = trace_return(res)
                log(trace_config.exit_func_with_return_val(func, converted))
            else:
                log(trace_config.exit_func_without_return_val(func))
            return res

        return wrapper

    return decorator


def _make_trace(
    args: Sequence[Any],
    kwargs: Dict[str, Callable],
    *,
    trace_return: Optional[Callable],
    trace_config: TraceConfig,
    trace_enable: bool,
):
    if trace_enable:
        if len(args) == 1 and callable(args[0]):
            return make_decorator([], {}, trace_return, trace_config)(args[0])
        else:
            return make_decorator(args, kwargs, trace_return, trace_config)
    else:
        if len(args) == 1 and callable(args[0]):
            return args[0]
        else:
            return lambda func: func


def make_trace(**kwargs):
    trace_config = TraceConfig(**kwargs)
    trace_en = trace_config.trace_enable()

    def trace(
        *args, _trace_return_=trace_config.default_str_conversion, **kwargs
    ) -> Callable:
        return _make_trace(
            args,
            kwargs,
            trace_return=_trace_return_,
            trace_config=trace_config,
            trace_enable=trace_en,
        )

    return trace


trace = make_trace()  # default case
