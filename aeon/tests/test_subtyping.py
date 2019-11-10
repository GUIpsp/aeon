import unittest

from ..types import *
from ..frontend2 import expr, typee
from ..typechecker.subtyping import SubtypingException, is_subtype

ex = expr.parse_strict
ty = typee.parse_strict


class TestTypeChecking(unittest.TestCase):
    def setUp(self):
        self.ctx = TypingContext()
        self.ctx.setup()

    def assert_st(self, sub, sup):
        if type(sub) == str:
            sub = ty(sub)
        if type(sup) == str:
            sup = ty(sup)
        if not is_subtype(self.ctx, sub, sup):
            raise AssertionError(sub, "is not subtype of", sup)

    def test_bottom_top(self):
        self.assert_st(ty("Bottom"), ty("Boolean"))
        self.assert_st(ty("Boolean"), ty("Top"))
        self.assert_st(ty("Bottom"), ty("Top"))

    def test_basic(self):
        self.assert_st(ty("Boolean"), ty("Boolean"))
        self.assert_st(ty("Integer"), ty("Integer"))

    def test_refined(self):
        self.assert_st(ty("{x:Integer where true}"), ty("Integer"))
        self.assert_st(ty("{x:Boolean where x}"), ty("Boolean"))
        self.assert_st(ty("Boolean"), ty("{x:Boolean where true}"))

    def test_refined_entails(self):
        self.assert_st(ty("{x:Boolean where (5 == 5)}"), ty("Boolean"))
        self.assert_st(ty("{x:Boolean where (5 == 5)}"),
                       ty("{x:Boolean where (true)}"))
        self.assert_st(ty("{x:{y:Boolean where true} where (5 == 5)}"),
                       ty("{x:Boolean where true}"))

        self.assert_st(ty("{x:Integer where (x == 5)}"),
                       ty("{v:Integer where (v > 4)}"))

        self.assert_st(ty("{x:Integer where (x > 5)}"),
                       ty("{k:Integer where (k > 4)}"))

        self.assert_st(ty("{x:Integer where (x > 5)}"),
                       ty("{k:Integer where (!(k < 4))}"))

        self.assert_st(ty("{x:Boolean where x}"), ty("{x:Boolean where true}"))
        self.assert_st(ty("{x:Boolean where true}"),
                       ty("{x:Boolean where ((x === true) || (x === false))}"))
        self.assert_st(ty("{y:Boolean where y}"), ty("{x:Boolean where x}"))

        self.assert_st(ty("{x:{y:Integer where (y < 5)} where (x == 0)}"),
                       ty("{x:Integer where (x==0)}"))

    def test_abs(self):
        self.assert_st(ty("(z:Integer) -> {y:Boolean where y}"),
                       ty("(k:Integer) -> {x:Boolean where x}"))
        self.assert_st(ty("(a:Integer) -> {b:Integer where (b > 1)}"),
                       ty("(k:Integer) -> {x:Integer where (x > 0)}"))

        self.assert_st(
            ty("(a:{v:Integer where (v > 0) }) -> {b:Integer where (b > 1)}"),
            ty("(k:{z:Integer where (z > 5) }) -> {x:Integer where (x > 0)}"))

        with self.assertRaises(SubtypingException):
            self.assert_st(ty("(a:Integer) -> {r:Integer where (r == a)}"),
                           ty("(a:Integer) -> (b:Integer) -> Bool"))
