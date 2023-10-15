from __future__ import annotations
from typing import Generic, TypeVar, Dict, Any, Type

T = TypeVar("T", contravariant=True)
Tp = TypeVar("Tp")

class Scope(Generic[T]):
    __slots__ = 'name', '_deps'

    def __init__(self, name: str) -> None:
        self.name = name
        self._deps: Dict[Any, Any] = {}

    def __getitem__(self, tp: Type[Tp]) -> Tp:
        return self._deps[tp]

    def use(self, tp: Type[Tp], value: Tp) -> Scope[T | Tp]:
        scope = Scope[T | Tp](self.name)
        scope._deps[tp] = {tp: value, **self._deps}
        return scope
    
    def __or__(self, rhs: Scope[Tp]) -> Scope[T | Tp]:
        scope = Scope[T | Tp](self.name)
        scope._deps = {**self._deps, **rhs._deps}

        return scope
    
    def __matmul__(self, new_name: str) -> Scope[T]:
        sc = Scope[T](new_name)
        sc._deps = {**sc._deps}

        return sc
    
    def __repr__(self) -> str:
        return f"<Scope {self.name}>"


class ScopeInitializer:
    __slots__ = 'name'

    def __init__(self, name: str) -> None:
        self.name = name

    def use(self, tp: Type[Tp], value: Tp) -> Scope[Tp]:
        return Scope(self.name).use(tp, value)


def scope(name: str) -> ScopeInitializer:
    return ScopeInitializer(name)


__all__ = ["Scope", "scope", "ScopeInitializer"]
