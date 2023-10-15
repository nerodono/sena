from typing import Callable, TypeVar, ParamSpec, Generic

P = ParamSpec("P")
T = TypeVar("T")


class _NamedFn(Generic[P, T]):
    __slots__ = "_fn", "__name__"

    def __init__(self, fn: Callable[P, T], name: str) -> None:
        self._fn = fn
        self.__name__ = name

    def __call__(self, *args: P.args, **kwds: P.kwargs) -> T:
        return self._fn(*args, **kwds)


def name_fn(v: Callable[P, T], name: str) -> Callable[P, T]:
    return _NamedFn(v, name)

def name_or_repr(v: Callable) -> str:
    if hasattr(v, '__name__'):
        return str(v.__name__)
    return repr(v)

def identity(v: T) -> T:
    return v

__all__ = ["name_or_repr", "identity",
           "name_fn"]
