from typing import Generic, TypeVar

from .di.scope import Scope

class Nil:
    ...

T = TypeVar("T")
T_contra = TypeVar("T_contra", contravariant=True)

class Context(Generic[T, T_contra]):
    __slots__ = 'event', 'scope'

    def __init__(self, event: T, scope: Scope[T_contra]) -> None:
        self.event = event
        self.scope = scope
