from __future__ import annotations

from typing import (Generic, TypeVar,
                    ParamSpec, TypeAlias,
                    Callable, Awaitable,
                    overload
                    )
from abc import ABCMeta, abstractmethod

from .utils.function import name_or_repr
from .utils.painter import is_awaitable_erased


P = ParamSpec("P")
NewP = ParamSpec("NewP")
T = TypeVar("T")

RetT = TypeVar("RetT", bool, Awaitable[bool])

FilterFn: TypeAlias = Callable[P, RetT]

Sync: TypeAlias = T
Async: TypeAlias = Awaitable[T]

Lifter: TypeAlias = Callable[[FilterFn[P, RetT]],
                             FilterFn[NewP, RetT]]

ApplicableFilter: TypeAlias = 'Filter[[T], RetT]'

class LifterWrapper(Generic[P, RetT, NewP]):
    __slots__ = "lifter",

    def __init__(self, lifter: Lifter[P, RetT, NewP]) -> None:
        self.lifter: Lifter[P, RetT, NewP] = lifter


def lift(lifter: Lifter[P, RetT, NewP]) -> LifterWrapper[P, RetT, NewP]:
    return LifterWrapper(lifter)


class Filter(Generic[P, RetT], metaclass=ABCMeta):
    @abstractmethod
    def lift(self, lifter: Lifter[P, RetT, NewP]) -> Filter[NewP, RetT]:
        raise NotImplementedError

    @abstractmethod
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RetT:
        raise NotImplementedError
    
    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError
    
    @overload
    def __and__(self, rhs: FilterFn[P, RetT]) -> And[P, RetT]:
        ...
    
    @overload
    def __and__(self, rhs: LifterWrapper[P, RetT, NewP]) -> Filter[NewP, RetT]:
        ...

    def __and__(self, rhs: FilterFn[P, RetT] | LifterWrapper[P, RetT, NewP]
                ) -> And[P, RetT] | Filter[NewP, RetT]:
        if isinstance(rhs, LifterWrapper):
            return self.lift(rhs.lifter)
        return And(self, rhs)


async def _async_and_impl(lhs: Awaitable[bool], rhs: Awaitable[bool]) -> bool:
    if await lhs:
        return await rhs
    return False


class And(Filter[P, RetT]):
    __slots__ = "_lhs", "_rhs"

    def __init__(self, lhs: FilterFn[P, RetT], rhs: FilterFn[P, RetT]) -> None:
        self._lhs: FilterFn[P, RetT] = lhs
        self._rhs: FilterFn[P, RetT] = rhs

    def lift(self, lifter: Lifter[P, RetT, NewP]
             ) -> And[NewP, RetT]:
        return And(lifter(self._lhs), lifter(self._rhs))
    
    def __repr__(self) -> str:
        return f"{name_or_repr(self._lhs)} & {name_or_repr(self._rhs)}"

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RetT:
        lhs = self._lhs(*args, **kwargs)
        rhs = self._rhs

        if is_awaitable_erased(lhs, rhs):
            # for some reason mypy doesn't understand this TypeGuard cast
            # :shrug:
            return _async_and_impl(lhs, rhs(*args, **kwargs)) # type: ignore
        return lhs and rhs(*args, **kwargs)
            


class Predicate(Filter[P, RetT]):
    __slots__ = "_fn",

    def __init__(self, fn: FilterFn[P, RetT]) -> None:
        self._fn: FilterFn[P, RetT] = fn

    def lift(self, lifter: Lifter[P, RetT, NewP]
             ) -> Predicate[NewP, RetT]:
        return Predicate(lifter(self._fn))
    
    def __repr__(self) -> str:
        return name_or_repr(self._fn)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RetT:
        return self._fn(*args, **kwargs)
