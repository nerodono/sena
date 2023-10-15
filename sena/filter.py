from __future__ import annotations

from typing import (Generic, TypeVar,
                    ParamSpec, TypeAlias,
                    Callable, Awaitable,
                    overload
                    )
from abc import ABCMeta, abstractmethod

from .utils.function import name_or_repr
from .utils.painter import is_awaitable_erased
from .utils.typefuck import SyncVal, AsyncVal, NonConstructible

class Exclusive(NonConstructible):
    ...
class Plain(NonConstructible):
    ...

P = ParamSpec("P")
NewP = ParamSpec("NewP")
T = TypeVar("T")

RetT = TypeVar("RetT", bool, Awaitable[bool])

FilterFn: TypeAlias = Callable[P, RetT]

Sync: TypeAlias = SyncVal[bool]
Async: TypeAlias = AsyncVal[bool]
Excl = TypeVar("Excl", Exclusive, Plain)

Lifter: TypeAlias = Callable[[FilterFn[P, RetT]],
                             FilterFn[NewP, RetT]]

ApplicableFilter: TypeAlias = FilterFn[[T], RetT]

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
    
    def __or__(self, rhs: FilterFn[P, RetT]) -> Or[P, RetT, Plain]:
        return Or(self, rhs)
    
    def __xor__(self, rhs: FilterFn[P, RetT]) -> Or[P, RetT, Exclusive]:
        return Or(self, rhs, True)

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
    
    def __invert__(self) -> Not[P, RetT]:
        return Not(self)


class BinaryFilter(Filter[P, RetT]):
    def __init__(self, lhs: FilterFn[P, RetT], rhs: FilterFn[P, RetT]) -> None:
        self._lhs: FilterFn[P, RetT] = lhs
        self._rhs: FilterFn[P, RetT] = rhs


async def _async_and_impl(lhs: Awaitable[bool], rhs: Awaitable[bool]) -> bool:
    if await lhs:
        return await rhs
    return False

async def _async_not_impl(rhs: Awaitable[bool]) -> bool:
    return not await rhs

async def _async_eor_impl(lhs: Awaitable[bool], rhs: Awaitable[bool]) -> bool:
    if await lhs:
        return not await rhs
    return await rhs

async def _async_or_impl(lhs: Awaitable[bool], rhs: Awaitable[bool]) -> bool:
    if await lhs:
        return True
    return await rhs

class Or(Generic[P, RetT, Excl], BinaryFilter[P, RetT]):
    __slots__ = "_lhs", "_rhs", "_exclusive"

    def __init__(self, lhs: FilterFn[P, RetT], rhs: FilterFn[P, RetT],
                 exclusive: bool = False) -> None:
        BinaryFilter.__init__(self, lhs, rhs)
        self._exclusive = exclusive
    
    @property
    def operator(self) -> str:
        if self._exclusive:
            return '^'
        return '*'
    
    def __repr__(self) -> str:
        return f"({name_or_repr(self._lhs)} {self.operator} {name_or_repr(self._rhs)})"
    
    def lift(self, lifter: Lifter[P, RetT, NewP]) -> Or[NewP, RetT, Excl]:
        return Or(lifter(self._lhs), lifter(self._rhs), self._exclusive)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RetT:
        lhs = self._lhs(*args, **kwargs)
        if is_awaitable_erased(lhs):
            lhs: Awaitable[bool] # type: ignore
            rhs: Awaitable[bool] = self._rhs(*args, **kwargs) # type: ignore

            if self._exclusive:
                return _async_eor_impl(lhs, rhs) # type: ignore
            return _async_or_impl(lhs, rhs) # type: ignore
        if self._exclusive:
            return lhs ^ self._rhs(*args, **kwargs) # type: ignore
        return lhs or self._rhs(*args, **kwargs)
            

class Not(Filter[P, RetT]):
    __slots__ = "_rhs",

    def __init__(self, rhs: FilterFn[P, RetT]) -> None:
        self._rhs: FilterFn[P, RetT] = rhs
    

    def lift(self, lifter: Lifter[P, RetT, NewP]) -> Not[NewP, RetT]:
        return Not(lifter(self._rhs))

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RetT:
        rhs = self._rhs(*args, **kwargs)
        if is_awaitable_erased(rhs):
            return _async_not_impl(rhs) # type: ignore
        else:
            return not rhs # type: ignore

    def __repr__(self) -> str:
        return f"~({name_or_repr(self._rhs)})"

class And(BinaryFilter[P, RetT]):
    __slots__ = "_lhs", "_rhs"

    def lift(self, lifter: Lifter[P, RetT, NewP]
             ) -> And[NewP, RetT]:
        return And(lifter(self._lhs), lifter(self._rhs))
    
    def __repr__(self) -> str:
        return f"{name_or_repr(self._lhs)} & {name_or_repr(self._rhs)}"

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RetT:
        lhs = self._lhs(*args, **kwargs)
        rhs = self._rhs

        if is_awaitable_erased(lhs):
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
