# trace-to-log

A simple library to add some logging of selected functions via a `trace`
decorator.

Example:

```python
@trace
def adder(x:int, y:int) -> int:
    return x + y
```
