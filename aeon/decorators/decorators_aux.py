from __future__ import annotations


from aeon.core.terms import Abstraction
from aeon.core.terms import Application
from aeon.core.terms import Let
from aeon.core.terms import Rec
from aeon.core.terms import Term
from aeon.core.terms import Var
from aeon.core.types import AbstractionType
from aeon.core.types import BaseType
from aeon.utils.ast_helpers import ensure_anf_app
from aeon.utils.ast_helpers import ensure_anf_rec

forall_functions_types = {
    "forAllInts": AbstractionType(var_name="x", var_type=BaseType(name="Int"), type=BaseType(name="Bool")),
    "forAllFloats": AbstractionType(var_name="x", var_type=BaseType(name="Float"), type=BaseType(name="Bool")),
    "forAllLists": AbstractionType(var_name="x", var_type=BaseType(name="List"), type=BaseType(name="Bool")),
}

# TODO Eduardo: Docstrings. handle_term is not very understandable.


class FreshHelper:
    """Helper class to generate fresh names for ANF transformation.

    This class is used to generate fresh names for variables during
    the ANF (A-normal form) transformation process.
    """

    def __init__(self):
        self.counter = 0

    def fresh(self) -> str:
        self.counter += 1
        return f"_anf_fitness_{self.counter}"

    def __call__(self, *args, **kwargs):
        return self.fresh()


fresh = FreshHelper()


def handle_term(term: Term) -> Term:
    """Transforms a given term into a Fitness function."""
    if isinstance(term, Let):
        return _handle_let(term)

    return term


def _handle_let(term: Let) -> Term:
    """Handles Let terms during transformation to Fitness function
    If the let represents an application of an abstraction, it is transformed into a Rec term that states the
    type of the abstraction, otherwise it stays the same.
    """

    if isinstance(term.body, Application) and isinstance(term.var_value, Abstraction):
        # this is needed because aeon cannot infer the type of the abstraction
        return _handle_abstraction_application(term)

    return term


def _handle_abstraction_application(term: Let) -> Term:
    """This receives a Term let with the application of an abstraction.
    This method forces the type of the abstraction because aeon can not infer the type of the abstraction.

    """
    assert isinstance(term.body, Application) and isinstance(term.body.fun, Var)

    abs_type = get_abstraction_type(term.body.fun)

    fitness_return = Application(arg=Var(f"{term.var_name}"), fun=Var(f"{term.body.fun.name}"))

    rec_term = Rec(
        var_name=f"{term.var_name}",
        var_type=abs_type,
        var_value=term.var_value,
        body=fitness_return,
    )

    return ensure_anf_rec(
        rec_term,
    )


def _transform_to_aeon_list(handled_terms: list[Term]) -> Term:
    """Transforms a list of individual handled terms to a single Term representing an Aeon list.

    Args:
        handled_terms (list[Term]): The list of handled terms.

    Returns:
        Term: Aeon list.
    """
    return_list_terms = [
        rec.body for rec in handled_terms if isinstance(rec, Rec) and isinstance(rec.body, Application)
    ]

    return_aeon_list: Term = Var("List_new")
    for term in return_list_terms:
        return_aeon_list = ensure_anf_app(
            fresh,
            Application(ensure_anf_app(fresh, Application(Var("List_append_float"), return_aeon_list)), term),
        )

    nested_rec = return_aeon_list
    for current_rec in handled_terms[::-1]:
        if isinstance(current_rec, Rec):
            nested_rec = Rec(current_rec.var_name, current_rec.var_type, current_rec.var_value, nested_rec)
        else:
            raise Exception(f"Not handled: {current_rec}")
    return nested_rec


def handle_multi_property_based_test(terms: list[Term]) -> Term:
    """Transforms a given list of terms into a Fitness function.

    Args:
        terms (list[Term]): The list of terms to be handled.

    Returns:
        tuple[Term, list[bool]]: The transformed terms in form of fitness functions
    """
    handled_terms = [handle_term(term) for term in terms]
    fitness_body = _transform_to_aeon_list(handled_terms)
    # fitness_body = _transform_to_aeon_list(terms)
    return fitness_body


def get_abstraction_type(term: Term) -> AbstractionType:
    """Obtain the abstraction type of the  known functions ."""
    assert isinstance(term, Var)
    if term.name in forall_functions_types:
        return forall_functions_types[term.name]

    raise Exception(f"Unknown function: {term}")
