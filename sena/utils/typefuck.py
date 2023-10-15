from typing import TypeAlias, Awaitable, TypeVar

T = TypeVar("T")

SyncVal: TypeAlias = T
AsyncVal: TypeAlias = Awaitable[T]

class NonConstructible:
    __slots__ = ()
    def __init__(self) -> None:
        raise TypeError("This type is non-constructible")


__all__ = ["NonConstructible", "SyncVal",
           "AsyncVal"]
