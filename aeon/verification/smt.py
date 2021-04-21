from z3.z3 import (
    Bool,
    And,
    BoolRef,
    BoolSort,
    DeclareSort,
    ExprRef,
    IntSort,
    Not,
    Or,
    String,
    Implies,
    ForAll,
    StringSort,
    Const,
)
from aeon.core.types import AbstractionType, BaseType, TypeVar, t_int, t_bool, t_string
from typing import Any, Callable, Dict, Generator, List, Tuple, Union
from aeon.core.liquid import (
    LiquidApp,
    LiquidHole,
    LiquidLiteralBool,
    LiquidLiteralInt,
    LiquidLiteralString,
    LiquidTerm,
    LiquidVar,
)
from aeon.core.liquid_ops import mk_liquid_and
from aeon.verification.vcs import (
    Conjunction,
    Constraint,
    Implication,
    LiquidConstraint,
)
from aeon.utils.time_utils import measure
from z3 import Solver, Int, sat, unsat, And, Not, unknown

base_functions: Dict[str, Any] = {
    "==": lambda x, y: x == y,
    "!=": lambda x, y: x != y,
    "<": lambda x, y: x < y,
    "<=": lambda x, y: x <= y,
    ">": lambda x, y: x > y,
    ">=": lambda x, y: x >= y,
    "!": lambda x: Not(x),
    "&&": lambda x, y: And(x, y),
    "||": lambda x, y: Or(x, y),
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
    "*": lambda x, y: x * y,
    "%": lambda x, y: x % y,
    "-->": lambda x, y: Implies(x, y),
}


class CanonicConstraint(object):
    binders: List[Tuple[str, BaseType]]
    pre: LiquidTerm
    pos: LiquidTerm

    def __init__(
        self,
        binders: List[Tuple[str, BaseType]],
        pre: LiquidTerm,
        pos: LiquidTerm,
    ):
        self.binders = binders
        self.pre = pre
        self.pos = pos

    def __repr__(self):
        return "\\forall {}, {} => {}".format(self.binders, self.pre, self.pos)


def flatten(c: Constraint) -> Generator[CanonicConstraint, None, None]:
    if isinstance(c, Conjunction):
        yield from flatten(c.c1)
        yield from flatten(c.c2)
    elif isinstance(c, Implication):
        for sub in flatten(c.seq):
            yield CanonicConstraint(
                binders=sub.binders + [(c.name, c.base)],
                pre=mk_liquid_and(sub.pre, c.pred),
                pos=sub.pos,
            )
    elif isinstance(c, LiquidConstraint):
        yield CanonicConstraint(binders=[], pre=LiquidLiteralBool(True), pos=c.expr)


s = Solver()
s.set(timeout=200),


def smt_valid(c: Constraint, foralls: List[Tuple[str, Any]] = []) -> bool:
    """ Verifies if a constraint is true using Z3 """
    cons: List[CanonicConstraint] = list(flatten(c))

    forall_vars = [
        (f[0], make_variable(f[0], f[1])) for f in foralls if isinstance(f[1], BaseType)
    ]

    for c in cons:
        s.push()
        smt_c = translate(c, extra=forall_vars)
        for _, v in forall_vars:
            smt_c = ForAll(v, smt_c)
        s.add(smt_c)
        result = s.check()
        s.pop()
        if result == sat:
            return False
        elif result == unknown:
            return False

    return True


def type_of_variable(variables: List[Tuple[str, Any]], name: str) -> Any:
    for (na, ref) in variables:
        if na == name:
            return ref
    print("Failed to load ", name, "from", [x[0] for x in variables])
    assert False


sort_cache = {}


def get_sort(base: BaseType) -> Any:
    if base == t_int:
        return IntSort
    elif base == t_bool:
        return BoolSort
    elif base == t_string:
        return StringSort
    elif isinstance(base, BaseType):
        if base.name not in sort_cache:
            sort_cache[base.name] = DeclareSort(base.name)
        return sort_cache[base.name]
    print("NO sort:", base)
    assert False


def make_variable(name: str, base: BaseType) -> Any:
    if base == t_int:
        return Int(name)
    elif base == t_bool:
        return Bool(name)
    elif base == t_string:
        return String(name)
    elif isinstance(base, BaseType):
        return Const(name, get_sort(base))

    print("NO var:", name, base, type(base))
    assert False


def translate_liq(t: LiquidTerm, variables: List[Tuple[str, Any]]):
    if isinstance(t, LiquidLiteralBool):
        return t.value
    elif isinstance(t, LiquidLiteralInt):
        return t.value
    elif isinstance(t, LiquidLiteralString):
        return t.value
    elif isinstance(t, LiquidVar):
        return type_of_variable(variables, t.name)
    elif isinstance(t, LiquidHole):
        assert False  # LiquidHoles should not get to SMT solver!
    elif isinstance(t, LiquidApp):
        f = None
        if t.fun in base_functions:
            f = base_functions[t.fun]
        else:
            for v in variables:
                if v[0] == t.fun and isinstance(v[1], function):
                    f = v[1]
        if not f:
            print("Failed to find t.fun", t.fun)
            assert False
        args = [translate_liq(a, variables) for a in t.args]
        return f(*args)
    assert False


"""
def make_variable_abs(name: str, abs: AbstractionType) -> Callable[[ExprRef], ExprRef]:

    return None


def translate_context(
    binders: List[Tuple[str, BaseType]]
) -> Generator[Tuple[str, Any], None, None]:
    for (name, base) in binders:
        if isinstance(base, BaseType):
            yield (name, make_variable(name, base))
        elif isinstance(base, AbstractionType):
            yield (name, make_variable_abs(name, base))
        else:
            assert False
"""


def translate(
    c: CanonicConstraint, extra=List[Tuple[str, Any]]
) -> Union[BoolRef, bool]:
    variables = [
        (name, make_variable(name, base))
        for (name, base) in c.binders
        if isinstance(base, BaseType)
    ] + extra
    e1 = translate_liq(c.pre, variables)
    e2 = translate_liq(c.pos, variables)
    if isinstance(e1, bool) and isinstance(e2, bool):
        return e1 and not e2
    return And(e1, Not(e2))
