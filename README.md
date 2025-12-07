# trace-to-log

A simple library to add some logging of selected functions via a `trace`
decorator.

By default, tracing is only enabled if `TRACE_ME` environment variable is set

Example:

```python
from trace_to_log import trace

@trace('*')
def adder(x:int, y:int) -> int:
    return x + y
```

Note, the '*' argument means all arguments should be logged. Otherwise, no
arguments are logged.

Now, calling `adder` will result in the following log entries at DEBUG level:

```
Going to call adder with args:
x :: 1
y :: 2
adder took 9.5367431640625e-07 seconds
Finished adder, returned:3
```

## being picky

If you don't want to log every argument, maybe because the string representation
of one of the objects is verbose, you can explicitly select which arguments
to log:

```python
from trace_to_log import trace

@trace('x')
def adder(x:int, y:int) -> int:
    return x + y
```

This will result in:

```
Going to call adder with args:
x :: 1
adder took 9.5367431640625e-07 seconds
Finished adder, returned:3
```

## custom argument conversions

Make log interpretation easier with a custom representation:

```python
from trace_to_log import trace

to_hex = lambda x: format(x, '#010x')

@trace('value', address=to_hex)
def write_32(address:int, value:int):
    pass
```

This will result in:

```
Going to call write_32 with args:
address :: 0x20000000
value :: 12"
write_32 took 1.6689300537109375e-06 seconds
Finished write_32, returned:None
```


## Unconditionally enabling tracing

```python
from trace_to_log import make_trace

trace = make_trace(
    trace_enable=lambda: True,
)

@trace('*')
def adder(x:int, y:int) -> int:
    return x + y
```
