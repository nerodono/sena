from typing import (TypeVar, Callable,
                    Generic, TypeGuard,
                    Any, Awaitable,
                    ParamSpec, Generator
                    )
from inspect import iscoroutine

T = TypeVar("T")
Ret = TypeVar("Ret")
P = ParamSpec("P")

class _RedResult(Generic[Ret]):
    __slots__ = ("_value", )

    def __init__(self, value: Ret) -> None:
        self._value = value

    def __await__(self) -> Generator[Any, None, Ret]:
        return self._value
        yield None
    
    def __repr__(self) -> str:
        return f"<Painted :result={self._value!r}>"


class RedCallable(Generic[P, Ret]):
    __slots__ = "_fn",

    def __init__(self, fn: Callable[P, Ret]) -> None:
        self._fn = fn

    def __call__(self, *args: P.args, **kwds: P.kwargs) -> Awaitable[Ret]:
        return _RedResult(self._fn(*args, **kwds))

    def __repr__(self) -> str:
        return f"{self._fn!r}:red"


class _RedPainter:
    def __mul__(self, f: Callable[P, Ret]) -> RedCallable[P, Ret]:
        return RedCallable(f)
    
    def __rtruediv__(self, red: RedCallable[P, Ret]) -> Callable[P, Ret]:
        return red._fn

    __rdiv__ = __rtruediv__

    def __repr__(self) -> str:
        return "<Red :painter :eraser>"



red = _RedPainter()

def is_awaitable_erased(obj: Any) -> TypeGuard[Awaitable[bool]]:
    return iscoroutine(obj)
