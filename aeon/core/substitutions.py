from ctypes import c_bool
from typing import List, Optional
from aeon.core.liquid import (
    LiquidApp,
    LiquidHole,
    LiquidLiteralBool,
    LiquidLiteralInt,
    LiquidLiteralString,
    LiquidTerm,
    LiquidVar,
)
from aeon.core.types import (
    AbstractionType,
    BaseType,
    Bottom,
    RefinedType,
    Top,
    Type,
    TypeVar,
    t_int,
    t_bool,
    t_string,
)
from aeon.core.terms import (
    Annotation,
    Hole,
    If,
    Rec,
    Term,
    Literal,
    Var,
    Application,
    Abstraction,
    Let,
)


def substitute_vartype(t: Type, rep: Type, name: str):

    def rec(k: Type):
        return substitute_vartype(k, rep, name)

    if isinstance(t, BaseType):
        return t
    elif isinstance(t, TypeVar) and t.name == name:
        return rep
    elif isinstance(t, TypeVar) and t.name != name:
        return t
    elif isinstance(t, RefinedType):
        return RefinedType(t.name, rec(t.type), t.refinement)
    elif isinstance(t, AbstractionType):
        return AbstractionType(t.var_name, rec(t.var_type), rec(t.type))
    assert False


def substitution_in_liquid(t: LiquidTerm, rep: LiquidTerm,
                           name: str) -> LiquidTerm:
    """ substitutes name in the term t with the new replacement term rep """
    assert isinstance(rep, LiquidTerm)
    if isinstance(t, LiquidLiteralInt):
        return t
    elif isinstance(t, LiquidLiteralBool):
        return t
    elif isinstance(t, LiquidLiteralString):
        return t
    elif isinstance(t, LiquidVar):
        if t.name == name:
            return rep
        else:
            return t
    elif isinstance(t, LiquidApp):
        return LiquidApp(
            t.fun, [substitution_in_liquid(a, rep, name) for a in t.args])
    elif isinstance(t, LiquidHole):
        if t.name == name:
            return rep
        else:
            return LiquidHole(
                t.name,
                [(substitution_in_liquid(a, rep, name), t)
                 for (a, t) in t.argtypes],
            )
    else:
        print(t, type(t))
        assert False


def substitution_in_type(t: Type, rep: Term, name: str) -> Type:
    replacement: LiquidTerm = liquefy(rep)
    if replacement is None:
        return t

    def rec(t: Type) -> Type:
        return substitution_in_type(t, rep, name)

    if isinstance(t, Top):
        return t
    elif isinstance(t, Bottom):
        return t
    elif isinstance(t, BaseType):
        return t
    elif isinstance(t, TypeVar):
        return t
    elif isinstance(t, AbstractionType):
        if isinstance(rep, Var) and rep.name == t.var_name:
            nname = t.var_name + "1"
            renamed = AbstractionType(
                nname, t.var_type,
                substitution_in_type(t.type, Var(nname), t.var_name))
            return substitution_in_type(renamed, rep, name)
        elif name == t.var_name:
            return t
        else:
            return AbstractionType(t.var_name, rec(t.var_type), rec(t.type))
    elif isinstance(t, RefinedType):
        if isinstance(rep, Var) and rep.name == t.name:
            nname = t.name + "1"
            renamed = RefinedType(
                nname,
                t.type,
                substitution_in_liquid(t.refinement, LiquidVar(nname), t.name),
            )
            return substitution_in_type(renamed, rep, name)
        elif t.name == name:
            return t
        else:
            return RefinedType(
                t.name, t.type,
                substitution_in_liquid(t.refinement, replacement, name))
    assert False


def substitution(t: Term, rep: Term, name: str) -> Term:

    def rec(x: Term):
        return substitution(x, rep, name)

    if isinstance(t, Literal):
        return t
    elif isinstance(t, Var):
        if t.name == name:
            return rep
        return t
    elif isinstance(t, Hole):
        if t.name == name:
            return rep
        return t
    elif isinstance(t, Application):
        return Application(fun=rec(t.fun), arg=rec(t.arg))
    elif isinstance(t, Abstraction):
        if t.var_name == name:
            return t
        else:
            return Abstraction(t.var_name, rec(t.body))
    elif isinstance(t, Let):
        if t.var_name == name:
            n_value = t.var_value
            n_body = t.body
        else:
            n_value = rec(t.var_value)
            n_body = rec(t.body)
        return Let(t.var_name, n_value, n_body)
    elif isinstance(t, Rec):
        if t.var_name == name:
            n_value = t.value
            n_body = t.body
        else:
            n_value = rec(t.value)
            n_body = rec(t.body)
        return Rec(t.var_name, t.var_type, n_value, n_body)
    elif isinstance(t, Annotation):
        return Annotation(rec(t.expr), type)
    assert False


def liquefy_app(app: Application) -> Optional[LiquidApp]:
    arg = liquefy(app.arg)
    if not arg:
        return None
    if isinstance(app.fun, Var):
        return LiquidApp(app.fun.name, [arg])
    elif isinstance(app.fun, Application):
        liquid_pseudo_fun = liquefy_app(app.fun)
        if liquid_pseudo_fun:
            return LiquidApp(liquid_pseudo_fun.fun,
                             liquid_pseudo_fun.args + [arg])
        return None
    elif isinstance(app.fun, Let):
        return liquefy_app(
            Application(
                substitution(app.fun.body, app.fun.var_value,
                             app.fun.var_name), app.arg))
    assert False


def liquefy_rec(t: Let) -> Optional[LiquidTerm]:
    value = liquefy(t.var_value)  # TODO
    body = liquefy(t.body)
    if value and body:
        return substitution_in_liquid(body, value, t.var_name)
    return None


def liquefy_let(t: Let) -> Optional[LiquidTerm]:
    value = liquefy(t.var_value)
    body = liquefy(t.body)
    if value and body:
        return substitution_in_liquid(body, value, t.var_name)
    return None


def liquefy_if(t: If) -> Optional[LiquidTerm]:
    co = liquefy(t.cond)
    th = liquefy(t.then)
    ot = liquefy(t.otherwise)
    if co and th and ot:
        return LiquidApp("ite", [co, th, ot])
    return None


def liquefy_ann(t: Annotation) -> Optional[LiquidTerm]:
    return liquefy(t.expr)


# patterm matching term
def liquefy(rep: Term) -> Optional[LiquidTerm]:
    if isinstance(rep, Literal) and rep.type == t_int:
        return LiquidLiteralInt(rep.value)
    elif isinstance(rep, Literal) and rep.type == t_bool:
        return LiquidLiteralBool(rep.value)
    elif isinstance(rep, Literal) and rep.type == t_string:
        return LiquidLiteralString(rep.value)
    elif isinstance(rep, Application):
        return liquefy_app(rep)
    elif isinstance(rep, Var):
        return LiquidVar(rep.name)
    elif isinstance(rep, Hole):
        return LiquidHole(rep.name)
    elif isinstance(rep, Let):
        return liquefy_let(rep)
    elif isinstance(rep, Rec):
        return liquefy_rec(rep)
    elif isinstance(rep, If):
        return liquefy_if(rep)
    elif isinstance(rep, Annotation):
        return liquefy_ann(rep)
    raise Exception(f"Unable to liquefy {rep}" + str(type(rep)))
    assert False
