from sena import Predicate, FilterFn, Sync
from sena import name_fn, lift

from sena.utils.function import name_or_repr


def divisible_by(by: int) -> Predicate[[int], Sync]:
    return Predicate(name_fn(lambda x: (x % by) == 0, f"divisble_by({by})"))

def lift_add(fn: FilterFn[[int], Sync]) -> FilterFn[[int, int], Sync]:
    return name_fn(lambda lhs, rhs: fn(lhs + rhs), name_or_repr(fn))

def nonzero(x: int, y: int) -> bool:
    return (x != 0) and (y != 0)


# Checks whether sum of two ints has 3, 5 and 2 divisors
f = (
      divisible_by(3)
    & divisible_by(5)
    & divisible_by(2)
    & lift(lift_add)
    & nonzero # two arguments should not be zero
)

true = 3 * 5 * 2
equation = f(true - 1, 1) and f(1, true - 1) and f(true//2, true//2)

assert(equation)
assert(not f(0, true))
assert(not f(true, 0))

print(f)
