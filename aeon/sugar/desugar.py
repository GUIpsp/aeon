from __future__ import annotations

import os.path
from pathlib import Path

from aeon.backend.evaluator import EvaluationContext
from aeon.core.substitutions import substitute_vartype
from aeon.core.substitutions import substitute_vartype_in_term
from aeon.core.terms import Abstraction
from aeon.core.terms import Application
from aeon.core.terms import Hole
from aeon.core.terms import Literal
from aeon.core.terms import Rec
from aeon.core.terms import Term
from aeon.core.terms import Var
from aeon.core.types import AbstractionType
from aeon.core.types import BaseType
from aeon.core.types import t_int
from aeon.prelude.prelude import evaluation_vars
from aeon.prelude.prelude import typing_vars
from aeon.sugar.parser import mk_parser
from aeon.sugar.program import Definition
from aeon.sugar.program import ImportAe
from aeon.sugar.program import Program
from aeon.sugar.program import TypeDecl
from aeon.synthesis_grammar.fitness import extract_fitness_from_synth
from aeon.typechecking.context import TypingContext
from aeon.typechecking.context import UninterpretedBinder
from aeon.utils.ctx_helpers import build_context


ProgramComponents = tuple[Term, TypingContext, EvaluationContext, list[bool] | None]


def desugar(p: Program) -> ProgramComponents:
    ctx, ectx = build_context(typing_vars), EvaluationContext(evaluation_vars)
    prog = determine_main_function(p)

    defs, type_decls = p.definitions, p.type_decls
    defs, type_decls = handle_imports(p.imports, defs, type_decls)

    if "fitness" in [d.name for d in defs]:
        minimize_flag = [True]
    else:
        minimize_flag = extract_and_add_fitness(defs)

    ctx, prog = update_program_and_context(prog, defs, ctx, type_decls)

    for tydeclname in type_decls:
        prog = substitute_vartype_in_term(prog, BaseType(tydeclname.name), tydeclname.name)

    return prog, ctx, ectx, minimize_flag


def determine_main_function(p: Program) -> Term:
    if "main" in [d.name for d in p.definitions]:
        return Application(Var("main"), Literal(1, type=t_int))
    return Hole("main")


def handle_imports(
    imports: list[ImportAe],
    defs: list[Definition],
    type_decls: list[TypeDecl],
) -> tuple[list[Definition], list[TypeDecl]]:
    for imp in imports[::-1]:
        import_p = handle_import(imp.path)
        defs_recursive, type_decls_recursive = [], []
        if import_p.imports:
            defs_recursive, type_decls_recursive = handle_imports(
                import_p.imports,
                import_p.definitions,
                import_p.type_decls,
            )
        defs = defs_recursive + import_p.definitions + defs
        type_decls = type_decls_recursive + import_p.type_decls + type_decls
    return defs, type_decls


def extract_and_add_fitness(defs: list[Definition]) -> list[bool] | None:
    synth_d = next((item for item in defs if item.name.startswith("synth")), None)
    if synth_d:
        fitness_function, minimize_flag = extract_fitness_from_synth(synth_d)
        defs.append(fitness_function)
        return minimize_flag
    return None


def update_program_and_context(
    prog: Term,
    defs: list[Definition],
    ctx: TypingContext,
    type_decls: list[TypeDecl],
) -> tuple[TypingContext, Term]:
    for d in defs[::-1]:
        if d.body == Var("uninterpreted"):
            ctx = handle_uninterpreted(ctx, d, type_decls)
        else:
            prog = bind_program_to_rec(prog, d)
    return ctx, prog


def handle_uninterpreted(ctx: TypingContext, d: Definition, type_decls: list[TypeDecl]) -> TypingContext:
    assert isinstance(d.type, AbstractionType)
    d_type = d.type
    for tyname in type_decls:
        d_type = substitute_vartype(d_type, BaseType(tyname.name), tyname.name)
    return UninterpretedBinder(ctx, d.name, d_type)


def bind_program_to_rec(prog: Term, d: Definition) -> Term:
    ty, body = d.type, d.body
    for arg_name, arg_type in d.args[::-1]:
        ty = AbstractionType(arg_name, arg_type, ty)
        body = Abstraction(arg_name, body)
    return Rec(d.name, ty, body, prog)


def handle_import(path: str) -> Program:
    """Imports a given path, following the precedence rules of current folder,
    AEONPATH."""
    possible_containers = (
        [Path.cwd()]
        + [Path.cwd() / "libraries"]
        + [Path(str) for str in os.environ.get("AEONPATH", ";").split(";") if str]
    )
    for container in possible_containers:
        file = container / f"{path}.ae"
        if file.exists():
            contents = open(file).read()
            return mk_parser("program").parse(contents)
    raise Exception(
        f"Could not import {path} in any of the following paths: " + ";".join([str(p) for p in possible_containers]),
    )
