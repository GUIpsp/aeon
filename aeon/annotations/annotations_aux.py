from __future__ import annotations

from aeon.core.terms import Abstraction
from aeon.core.terms import Application
from aeon.core.terms import Let
from aeon.core.terms import Rec
from aeon.core.terms import Term
from aeon.core.terms import Var
from aeon.core.types import AbstractionType
from aeon.core.types import BaseType


forall_functions_types = {
    "forAllInts": AbstractionType(type=BaseType(name="Bool"), var_name="x", var_type=BaseType(name="Int")),
    "forAllFloats": AbstractionType(type=BaseType(name="Bool"), var_name="x", var_type=BaseType(name="Float")),
    "forAllLists": AbstractionType(type=BaseType(name="Bool"), var_name="x", var_type=BaseType(name="List")),
}


def handle_term(term: Term, minimize_flag: bool | list[bool]) -> tuple[Term, bool | list[bool]]:
    if isinstance(term, Let):
        return _handle_let(term, minimize_flag)
    elif isinstance(term, Var):
        # TODO: handle Var type
        pass

    raise Exception(f"Term not handled by annotation: {type(term)}")


def _handle_let(term: Let, minimize_flag: bool | list[bool]) -> tuple[Term, bool | list[bool]]:
    if isinstance(term.body, Application):
        if isinstance(term.var_value, Abstraction):
            return _transform_to_fitness_term(term), minimize_flag
        else:
            return term, minimize_flag

    return term, minimize_flag


def _transform_to_fitness_term(term: Let) -> Term:
    abs_type = get_abstraction_type(term.body.fun)
    var_name_for_return = f"{term.body.fun}_return"

    fitness_return = Let(
        var_name=var_name_for_return,
        var_value=Application(arg=Var(f"{term.var_name}"), fun=Var(f"{term.body.fun.name}")),
        body=Var(var_name_for_return),
    )

    return Rec(
        var_name=f"{term.var_name}",
        var_type=abs_type,
        var_value=term.var_value,
        body=fitness_return,
    )


def handle_term(term: Term, minimize_flag: bool | list[bool]) -> tuple[Term, bool | list[bool]]:
    if isinstance(term, Let):
        if isinstance(term.body, Application):
            if isinstance(term.var_value, Abstraction):
                abs_type: AbstractionType = get_abstraction_type(term.body.fun)

                fitness_return = Let(
                    var_name=f" {term.body.fun}_return",
                    var_value=Application(arg=Var(f"{term.var_name}"), fun=Var(f"{term.body.fun.name}")),
                    body=Var(f" {term.body.fun}_return"),
                )

                fitness_term = Rec(
                    var_name=f"{term.var_name}",
                    var_type=abs_type,
                    var_value=term.var_value,
                    body=fitness_return,
                )

                return fitness_term, minimize_flag

        return term, minimize_flag
    elif isinstance(term, Var):
        # TODO: handle Var type
        pass
    raise Exception(f"Term not handled by annotation: {type(term)}")


def get_abstraction_type(term: Term) -> AbstractionType:
    if isinstance(term, Var):
        if term.name in forall_functions_types:
            return forall_functions_types[term.name]
    raise Exception(f"Not handled: {term}")
