import re
import os
import os.path
import copy
from functools import reduce
from parsec import *

from .ast import *
from .types import *

ext = 'ae'

type_aliases = {}

# ignore cases.
whitespace = regex(r'\s+', re.MULTILINE)
comment = regex(r'#.*')
ignore = many((whitespace | comment))

reserved_keywords = ['if', 'then', 'else']

# lexer for words.

lexeme = lambda p: p << ignore  # skip all ignored characters.

t = lambda k: lexeme(string(k))


def refined_value(v, t, label="_v"):
    tapp = TApplication(Var("=="), t)
    app1 = Application(tapp, Var(label))
    app2 = Application(app1, Literal(v, type=t))
    return RefinedType(label, t, app2)


@lexeme
@generate
def operators_definition():
    yield t("(")
    op = yield lexeme(regex(r'[\+=\>\<!\*\-&\|]{1,3}'))
    yield t(")")
    return op


@lexeme
@generate
def hole():
    yield t("[[")
    ty = yield typee
    yield t("]]")
    return Hole(type=ty)


def avoid_reserved_keywords(ks):
    def p(parsed):
        def f(text, index):
            if parsed in ks:
                return Value.failure(index, parsed + " word is reserved")
            return Value.success(index, parsed)

        return f

    return p


arrow = t('->')
fatarrow = t('=>')
true = t('true').parsecmap(lambda x: Literal(
    True, type=refined_value(True, t_b, "_v")))
false = t('false').parsecmap(lambda x: Literal(
    False, type=refined_value(False, t_b, "_v")))
null = t('null').result(Literal(None, type=t_o))
symbol = lexeme(regex(r'[.\d\w_]+')).bind(
    avoid_reserved_keywords(reserved_keywords)) ^ operators_definition

op_1 = t("*") ^ t("/") ^ t("%")
op_2 = t("+") ^ t("-")
op_3 = t("<=") ^ t("<") ^ t(">=") ^ t(">") ^ t("===") ^ t("!==") ^ t("==") ^ t(
    "!=") ^ t("-->")
op_4 = t("&&") ^ t("||")
op_5 = t("=")
op_all = op_4 ^ op_3 ^ op_2 ^ op_1


def number():
    '''Parse number.'''

    def fa(x):
        if "." not in x:
            return Literal(int(x), type=refined_value(int(x), t_i, "_v"))
        else:
            return Literal(float(x), type=copy.deepcopy(t_f))

    return lexeme(
        regex(r'(0|[1-9][0-9]*)([.][0-9]+)?([eE][+-]?[0-9]+)?')).parsecmap(fa)


def charseq():
    '''Parse string. (normal string and escaped string)'''

    def string_part():
        '''Parse normal string.'''
        return regex(r'[^"\\]+')

    def string_esc():
        '''Parse escaped string.'''
        return string('\\') >> (
            string('\\')
            | string('/')
            | string('b').result('\b')
            | string('f').result('\f')
            | string('n').result('\n')
            | string('r').result('\r')
            | string('t').result('\t')
            |
            regex(r'u[0-9a-fA-F]{4}').parsecmap(lambda s: chr(int(s[1:], 16))))

    return string_part() | string_esc()


@lexeme
@generate
def quoted():
    '''Parse quoted string.'''
    yield string('"')
    body = yield many(charseq())
    yield string('"')
    return ''.join(body)


@lexeme
@generate
def abstraction():
    yield t("\\")
    name = yield symbol
    yield t(":")
    ty = yield typee
    yield arrow
    e = yield expr
    return Abstraction(arg_name=name, arg_type=ty, body=e)


@lexeme
@generate
def tabstraction():
    tvar = yield symbol
    yield t(":")
    k = yield kind
    yield fatarrow
    e = yield expr
    return TAbstraction(tvar, k, e)


@lexeme
@generate
def tapplication():
    target = yield term
    yield t("[")
    ty = yield typee
    yield t("]")
    return TApplication(target, ty)


@lexeme
@generate
def ite():
    yield t("if")
    c = yield expr
    yield t("then")
    then = yield expr
    yield t("else")
    otherwise = yield expr
    return If(c, then, otherwise)


@lexeme
@generate
def expr_ops():
    a1 = yield expr
    op = yield op_all
    a2 = yield expr
    if op in ["==", "!=", "+", "-", "*", "/", "<", ">", "<=", ">="]:
        return Application(Application(TApplication(Var(op), t_delegate), a1),
                           a2)
    else:
        return Application(Application(Var(op), a1), a2)


@lexeme
@generate
def expr_wrapped():
    o = yield expr
    return o


@lexeme
@generate
def not_op():
    yield t("!")
    e = yield expr
    return Application(Var("!"), e)


var = symbol.parsecmap(lambda x: Var(x))
literal = true ^ false ^ null ^ number() ^ quoted
expr_basic = literal ^ var

term = hole | abstraction ^ tabstraction ^ expr_basic ^ not_op ^ (
    t("(") >> expr_wrapped << t(")")) ^ (t("(") >> expr_ops << t(")"))

expr_tapp = tapplication ^ term

expr_app = many1(
    expr_tapp).parsecmap(lambda xs: reduce(lambda x, y: Application(x, y), xs))

expr = ite | expr_app


@lexeme
@generate
def basic_type():
    b = yield symbol
    if b in type_aliases:
        return type_aliases[b]
    return BasicType(b)


@lexeme
@generate
def arrow_type():
    yield t("(")
    x = yield symbol
    yield t(":")
    t1 = yield typee
    yield t(")")
    yield arrow
    t2 = yield typee
    return AbstractionType(x, t1, t2)


@lexeme
@generate
def refined_type():
    yield t("{")
    x = yield symbol
    yield t(":")
    ty = yield typee
    yield t("where")
    cond = yield expr
    yield t("}")
    return RefinedType(x, ty, cond)


@lexeme
@generate
def type_abstraction():
    yield t("(")
    x = yield symbol
    yield t(":")
    k = yield kind
    yield t(")")
    yield fatarrow
    ty = yield typee
    return TypeAbstraction(x, k, ty)


@lexeme
@generate
def type_application():
    yield t("(")
    t1 = yield typee
    t2 = yield typee
    yield t(")")
    return TypeApplication(t1, t2)


@lexeme
@generate
def kind_rec():
    yield t("(")
    a = yield kind
    yield fatarrow
    b = yield kind
    yield t(")")
    return Kind(a, b)


@lexeme
@generate
def typee_wrapped():
    o = yield typee
    return o


kind = kind_rec ^ t("*").result(Kind())
typee = type_abstraction ^ arrow_type ^ (
    t("(") >> typee_wrapped <<
    t(")")) ^ refined_type ^ type_application ^ basic_type


@lexeme
@generate
def topleveldef():
    """ Top Level Definition: name : type = expr """
    name = yield symbol
    yield t(":")
    type_ = yield typee
    yield t("=")
    body = yield expr
    yield t(";")
    return Definition(name, type_, body)


@lexeme
@generate
def type_alias():
    '''Parse type alias.'''
    yield t("type")
    name = yield symbol
    aliased_type = yield (t("=") >> typee)
    type_aliases[name] = aliased_type
    return TypeAlias(name, aliased_type)


@lexeme
@generate
def type_declaration():
    '''Parse type alias.'''
    yield t("type")
    name = yield symbol
    yield t(":")
    k = yield kind
    return TypeDeclaration(name, k)


imprt = t('import') >> symbol.parsecmap(lambda x: Import(x))

program = ignore >> many(type_alias ^ type_declaration ^ topleveldef ^ imprt)

cached_imports = []


def resolve_imports(p, base_path=lambda x: x):
    n_p = []
    for n in p:
        if isinstance(n, Import):
            fname = n.name
            path = ""
            while fname.startswith(".."):
                fname = fname[2:]
                path = path + "../"
            path = path + fname.replace(".", "/")
            path = os.path.realpath(base_path(path))
            if path not in cached_imports:
                cached_imports.append(path)
                ip = parse(path)
                n_p.extend(ip.declarations)
        else:
            n_p.append(n)
    return n_p


def parse(fname):
    txt = open(fname).read()
    p = program.parse_strict(txt)
    p = resolve_imports(p,
                        base_path=lambda x: os.path.join(
                            os.path.dirname(fname), "{}.{}".format(x, ext)))
    return Program(p)